import io
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self, config):
        self.config = config
        self._client = None

    def _get_client(self):
        if self._client is None:
            import boto3
            kwargs = {
                "aws_access_key_id": self.config.s3_access_key,
                "aws_secret_access_key": self.config.s3_secret_key,
                "region_name": self.config.s3_region or "us-east-1",
            }
            if self.config.s3_endpoint:
                kwargs["endpoint_url"] = self.config.s3_endpoint
            self._client = boto3.client("s3", **kwargs)
        return self._client

    def reload(self):
        self._client = None

    def list_backups(self) -> List[Dict[str, Any]]:
        try:
            client = self._get_client()
            prefix = self.config.s3_prefix
            paginator = client.get_paginator("list_objects_v2")
            results = []
            for page in paginator.paginate(Bucket=self.config.s3_bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if not key.endswith(".tar"):
                        continue
                    slug = key[len(prefix):].removesuffix(".tar")
                    results.append({
                        "key": key,
                        "slug": slug,
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                    })
            return results
        except Exception as e:
            logger.error("S3 list_objects failed: %s", e)
            return []

    def upload(self, slug: str, data: bytes, name: str = "") -> bool:
        try:
            client = self._get_client()
            key = f"{self.config.s3_prefix}{slug}.tar"
            extra = {"Metadata": {"name": name}} if name else {}
            client.upload_fileobj(io.BytesIO(data), self.config.s3_bucket, key, ExtraArgs=extra)
            return True
        except Exception as e:
            logger.error("S3 upload failed for %s: %s", slug, e)
            return False

    def upload_file(self, slug: str, path: str, name: str = "") -> bool:
        try:
            client = self._get_client()
            key = f"{self.config.s3_prefix}{slug}.tar"
            extra = {"Metadata": {"name": name}} if name else {}
            client.upload_file(path, self.config.s3_bucket, key, ExtraArgs=extra)
            return True
        except Exception as e:
            logger.error("S3 upload_file failed for %s: %s", slug, e)
            return False

    def delete(self, slug: str) -> bool:
        try:
            client = self._get_client()
            key = f"{self.config.s3_prefix}{slug}.tar"
            client.delete_object(Bucket=self.config.s3_bucket, Key=key)
            return True
        except Exception as e:
            logger.error("S3 delete failed for %s: %s", slug, e)
            return False

    def test_connection(self) -> Dict[str, Any]:
        try:
            self._get_client().head_bucket(Bucket=self.config.s3_bucket)
            return {"ok": True, "bucket_exists": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
