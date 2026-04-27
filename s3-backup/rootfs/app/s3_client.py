import io
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self, config):
        self.config = config
        self._client = None

    def _sanitize_name_for_key(self, name: str, slug: str) -> str:
        """
        Sanitize a human-readable name to be safe for use as an S3 key.
        Falls back to slug if name is empty or becomes empty after sanitization.
        Appends slug suffix to ensure uniqueness.
        """
        if not name or name.isspace():
            return slug
        
        # Replace spaces with underscores and remove/replace problematic characters
        sanitized = re.sub(r'[^\w\-_\.]', '_', name.strip())
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # If sanitization left us with nothing, fall back to slug
        if not sanitized:
            return slug
        
        # Ensure uniqueness by appending a portion of the slug
        # Take first 8 characters of slug to keep it reasonably short
        slug_suffix = slug[:8] if len(slug) >= 8 else slug
        return f"{sanitized}_{slug_suffix}"

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
                    
                    filename = key[len(prefix):].removesuffix(".tar")
                    
                    # Get metadata to find the original slug and human-readable name
                    try:
                        head_response = client.head_object(Bucket=self.config.s3_bucket, Key=key)
                        metadata = head_response.get("Metadata", {})
                        
                        # If we have slug in metadata, this is a new-format upload with human-readable filename
                        if "slug" in metadata:
                            slug = metadata["slug"]
                            name = metadata.get("name", filename)
                        else:
                            # Legacy format: filename is the slug, name might be in metadata
                            slug = filename
                            name = metadata.get("name", filename)
                    except Exception as e:
                        logger.warning("Could not retrieve metadata for %s: %s", key, e)
                        # Fallback: assume filename is the slug
                        slug = filename
                        name = filename
                    
                    results.append({
                        "key": key,
                        "slug": slug,
                        "name": name,
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
            # Use human-readable name for the key if available, otherwise fall back to slug
            sanitized_name = self._sanitize_name_for_key(name, slug)
            key = f"{self.config.s3_prefix}{sanitized_name}.tar"
            
            # Store both the original slug and name in metadata
            extra = {
                "Metadata": {
                    "slug": slug,
                    "name": name or sanitized_name
                }
            }
            
            client.upload_fileobj(io.BytesIO(data), self.config.s3_bucket, key, ExtraArgs=extra)
            return True
        except Exception as e:
            logger.error("S3 upload failed for %s: %s", slug, e)
            return False

    def upload_file(self, slug: str, path: str, name: str = "") -> bool:
        try:
            client = self._get_client()
            # Use human-readable name for the key if available, otherwise fall back to slug
            sanitized_name = self._sanitize_name_for_key(name, slug)
            key = f"{self.config.s3_prefix}{sanitized_name}.tar"
            
            # Store both the original slug and name in metadata
            extra = {
                "Metadata": {
                    "slug": slug,
                    "name": name or sanitized_name
                }
            }
            
            client.upload_file(path, self.config.s3_bucket, key, ExtraArgs=extra)
            return True
        except Exception as e:
            logger.error("S3 upload_file failed for %s: %s", slug, e)
            return False

    def delete(self, slug: str) -> bool:
        try:
            client = self._get_client()
            
            # First, try to find the actual key for this slug
            # Since we may have backups stored with either slug-based or name-based keys
            backups = self.list_backups()
            backup_key = None
            
            for backup in backups:
                if backup["slug"] == slug:
                    backup_key = backup["key"]
                    break
            
            if backup_key:
                client.delete_object(Bucket=self.config.s3_bucket, Key=backup_key)
            else:
                # Fallback: try the old slug-based key format
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
