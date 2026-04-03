import logging
import os
import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BACKUP_DIR = "/backup"


class Coordinator:
    def __init__(self, config, ha, s3):
        self.config = config
        self.ha = ha
        self.s3 = s3
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {
            "last_backup": None,
            "next_backup": None,
            "last_sync": None,
            "syncing": False,
            "backing_up": False,
            "error": None,
            "backups": [],
            "ha_count": 0,
            "s3_count": 0,
        }

    def get_state(self) -> Dict[str, Any]:
        return dict(self._state)

    def reload_config(self, config):
        self.config = config
        self.ha.config = config
        self.s3.config = config
        self.s3.reload()

    # ------------------------------------------------------------------ #
    # Backup list                                                          #
    # ------------------------------------------------------------------ #

    def refresh_backups(self) -> List[Dict[str, Any]]:
        ha_list = self.ha.list_backups()
        s3_list = self.s3.list_backups() if self.config.is_s3_configured() else []

        s3_by_slug = {b["slug"]: b for b in s3_list}
        merged: List[Dict[str, Any]] = []

        for b in ha_list:
            slug = b.get("slug", "")
            s3_info = s3_by_slug.pop(slug, None)
            merged.append({
                "slug": slug,
                "name": b.get("name", slug),
                "date": b.get("date", ""),
                "size": b.get("size", 0),
                "type": b.get("type", "unknown"),
                "in_ha": True,
                "in_s3": s3_info is not None,
                "s3_size": s3_info["size"] if s3_info else 0,
                "s3_date": s3_info["last_modified"] if s3_info else "",
            })

        for slug, s3_info in s3_by_slug.items():
            merged.append({
                "slug": slug,
                "name": slug,
                "date": s3_info.get("last_modified", ""),
                "size": 0,
                "type": "unknown",
                "in_ha": False,
                "in_s3": True,
                "s3_size": s3_info.get("size", 0),
                "s3_date": s3_info.get("last_modified", ""),
            })

        merged.sort(key=lambda x: x.get("date", ""), reverse=True)

        self._state["backups"] = merged
        self._state["ha_count"] = sum(1 for b in merged if b["in_ha"])
        self._state["s3_count"] = sum(1 for b in merged if b["in_s3"])

        ha_backups = [b for b in merged if b["in_ha"]]
        if ha_backups:
            self._state["last_backup"] = ha_backups[0]["date"]

        self._update_next_backup()
        return merged

    def _update_next_backup(self):
        if not self.config.days_between_backups:
            self._state["next_backup"] = None
            return
        last = self._state.get("last_backup")
        if not last:
            self._state["next_backup"] = datetime.now(timezone.utc).isoformat()
            return
        try:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            self._state["next_backup"] = (last_dt + timedelta(days=self.config.days_between_backups)).isoformat()
        except Exception:
            self._state["next_backup"] = None

    # ------------------------------------------------------------------ #
    # Upload / Delete                                                      #
    # ------------------------------------------------------------------ #

    def upload_to_s3(self, slug: str) -> Dict[str, Any]:
        if not self.config.is_s3_configured():
            return {"error": "S3 not configured"}

        name = next((b["name"] for b in self._state["backups"] if b["slug"] == slug), slug)
        file_path = os.path.join(BACKUP_DIR, f"{slug}.tar")

        try:
            if os.path.exists(file_path):
                logger.info("Uploading %s from disk to S3", slug)
                ok = self.s3.upload_file(slug, file_path, name)
            else:
                logger.info("Downloading %s from supervisor then uploading to S3", slug)
                ok = self.s3.upload(slug, self.ha.download_backup(slug), name)

            if not ok:
                return {"error": "S3 upload failed"}

            if self.config.delete_after_upload:
                logger.info("Deleting %s from HA after upload", slug)
                self.ha.delete_backup(slug)

            self.refresh_backups()
            return {"ok": True, "slug": slug}
        except Exception as e:
            logger.error("upload_to_s3 failed: %s", e)
            return {"error": str(e)}

    def delete_from_ha(self, slug: str) -> Dict[str, Any]:
        if not self.ha.delete_backup(slug):
            return {"error": f"Failed to delete {slug} from HA"}
        self.refresh_backups()
        return {"ok": True}

    def delete_from_s3(self, slug: str) -> Dict[str, Any]:
        if not self.s3.delete(slug):
            return {"error": f"Failed to delete {slug} from S3"}
        self.refresh_backups()
        return {"ok": True}

    # ------------------------------------------------------------------ #
    # Backup creation                                                      #
    # ------------------------------------------------------------------ #

    def create_backup(self, name: Optional[str] = None) -> Dict[str, Any]:
        if self._state["backing_up"]:
            return {"error": "Backup already in progress"}

        with self._lock:
            self._state["backing_up"] = True
            self._state["error"] = None
            try:
                if not name:
                    name = f"Full Backup {datetime.now(timezone.utc):%Y-%m-%d %H:%M}"
                logger.info("Creating backup: %s", name)
                result = self.ha.create_backup(name)
                self._state["last_backup"] = datetime.now(timezone.utc).isoformat()
                self._update_next_backup()
                logger.info("Backup created: %s", result.get("slug", "?"))
                self.refresh_backups()
                return result
            except Exception as e:
                self._state["error"] = str(e)
                logger.error("create_backup failed: %s", e)
                return {"error": str(e)}
            finally:
                self._state["backing_up"] = False

    # ------------------------------------------------------------------ #
    # Sync                                                                 #
    # ------------------------------------------------------------------ #

    def sync(self) -> Dict[str, Any]:
        if self._state["syncing"]:
            return {"error": "Sync already in progress"}

        with self._lock:
            self._state["syncing"] = True
            self._state["error"] = None
            uploaded = 0
            try:
                logger.info("Sync started")
                backups = self.refresh_backups()

                if self.config.is_s3_configured():
                    for b in backups:
                        if b["in_ha"] and not b["in_s3"]:
                            result = self.upload_to_s3(b["slug"])
                            if "ok" in result:
                                uploaded += 1
                            else:
                                logger.warning("Upload failed for %s: %s", b["slug"], result.get("error"))

                backups = self.refresh_backups()

                ha_backups = [b for b in backups if b["in_ha"]]
                while len(ha_backups) > self.config.max_backups_in_ha:
                    oldest = ha_backups.pop()
                    logger.info("Pruning HA backup: %s", oldest["slug"])
                    self.ha.delete_backup(oldest["slug"])

                if self.config.max_backups_in_s3 > 0:
                    s3_backups = [b for b in backups if b["in_s3"]]
                    while len(s3_backups) > self.config.max_backups_in_s3:
                        oldest = s3_backups.pop()
                        logger.info("Pruning S3 backup: %s", oldest["slug"])
                        self.s3.delete(oldest["slug"])

                self._state["last_sync"] = datetime.now(timezone.utc).isoformat()
                self.refresh_backups()
                logger.info("Sync complete. Uploaded %d backup(s).", uploaded)
                return {"ok": True, "uploaded": uploaded}
            except Exception as e:
                self._state["error"] = str(e)
                logger.error("sync failed: %s", e)
                return {"error": str(e)}
            finally:
                self._state["syncing"] = False

    def is_backup_due(self) -> bool:
        if not self.config.days_between_backups:
            return False
        nxt = self._state.get("next_backup")
        if not nxt:
            return True
        try:
            return datetime.now(timezone.utc) >= datetime.fromisoformat(nxt.replace("Z", "+00:00"))
        except Exception:
            return False
