import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)


class HAClient:
    def __init__(self, config):
        self.config = config

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config.supervisor_token}"}

    def list_backups(self) -> List[Dict[str, Any]]:
        try:
            resp = requests.get(
                f"{self.config.supervisor_url}/backups",
                headers=self._headers(),
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("backups", [])
        except Exception as e:
            logger.error("Failed to list HA backups: %s", e)
            return []

    def create_backup(self, name: str) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.config.supervisor_url}/backups/new/full",
            headers=self._headers(),
            json={"name": name},
            timeout=3600,
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    def delete_backup(self, slug: str) -> bool:
        try:
            resp = requests.delete(
                f"{self.config.supervisor_url}/backups/{slug}",
                headers=self._headers(),
                timeout=30,
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error("Failed to delete HA backup %s: %s", slug, e)
            return False

    def download_backup(self, slug: str) -> bytes:
        resp = requests.get(
            f"{self.config.supervisor_url}/backups/{slug}/download",
            headers=self._headers(),
            timeout=3600,
        )
        resp.raise_for_status()
        return resp.content
