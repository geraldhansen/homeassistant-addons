import json
import os
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

OPTIONS_FILE = "/data/options.json"
USER_SETTINGS_FILE = "/data/user_settings.json"


@dataclass
class Config:
    s3_endpoint: str = ""
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_prefix: str = "ha-backups/"
    days_between_backups: int = 3
    max_backups_in_ha: int = 4
    max_backups_in_s3: int = 4
    delete_after_upload: bool = False
    log_level: str = "INFO"

    @classmethod
    def load(cls) -> "Config":
        data = {}
        for path in (OPTIONS_FILE, USER_SETTINGS_FILE):
            try:
                with open(path) as f:
                    data.update(json.load(f))
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.error("Error reading %s: %s", path, e)

        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def save(self):
        try:
            os.makedirs(os.path.dirname(USER_SETTINGS_FILE) or ".", exist_ok=True)
            with open(USER_SETTINGS_FILE, "w") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            logger.error("Error saving config: %s", e)

    def is_s3_configured(self) -> bool:
        return bool(self.s3_bucket and self.s3_access_key and self.s3_secret_key)

    @property
    def supervisor_token(self) -> str:
        return os.environ.get("SUPERVISOR_TOKEN", "")

    @property
    def supervisor_url(self) -> str:
        return os.environ.get("SUPERVISOR_URL", "http://supervisor")
