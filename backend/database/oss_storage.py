"""
MyAgent - OSS Storage Layer (Alibaba Cloud Object Storage)
Stores uploaded images, documents, and RAG files.
Falls back gracefully if OSS is unavailable.
"""

import base64
import hashlib
from datetime import datetime
from typing import Optional

from config import get_settings

try:
    import oss2
    _HAS_OSS = True
except ImportError:
    _HAS_OSS = False

_bucket = None
_oss_available = None

OSS_BUCKET_NAME = "myagent-hackaton-2026"
OSS_ENDPOINT = "oss-ap-southeast-1.aliyuncs.com"


def _get_bucket():
    """Get or create OSS bucket connection."""
    global _bucket, _oss_available

    if _oss_available is False:
        return None
    if _bucket is not None:
        return _bucket

    if not _HAS_OSS:
        _oss_available = False
        return None

    settings = get_settings()
    access_key = settings.alibaba_access_key_id
    secret_key = settings.alibaba_access_key_secret

    if not access_key or not secret_key:
        _oss_available = False
        return None

    try:
        auth = oss2.Auth(access_key, secret_key)
        _bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
        # Test connection
        _bucket.get_bucket_info()
        _oss_available = True
        print(f"✅ OSS: Connected (bucket: {OSS_BUCKET_NAME})")
        return _bucket
    except Exception as e:
        print(f"⚠️ OSS: Not available ({str(e)[:50]})")
        _oss_available = False
        return None


def is_oss_available() -> bool:
    """Check if OSS is connected."""
    _get_bucket()
    return _oss_available is True


def upload_image(image_base64: str, session_id: str = "", prefix: str = "images") -> Optional[str]:
    """
    Upload a base64-encoded image to OSS.
    Returns the public URL if successful, None otherwise.
    """
    bucket = _get_bucket()
    if not bucket:
        return None

    try:
        # Decode base64
        if ";base64," in image_base64:
            image_data = base64.b64decode(image_base64.split(";base64,")[1])
        else:
            image_data = base64.b64decode(image_base64)

        # Generate unique filename
        hash_id = hashlib.md5(image_data[:1024]).hexdigest()[:12]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}/{session_id}/{timestamp}_{hash_id}.jpg"

        # Upload
        bucket.put_object(filename, image_data)

        # Return public URL
        url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{filename}"
        return url
    except Exception:
        return None


def upload_document(content: bytes, filename: str, prefix: str = "documents") -> Optional[str]:
    """Upload a document to OSS."""
    bucket = _get_bucket()
    if not bucket:
        return None

    try:
        key = f"{prefix}/{filename}"
        bucket.put_object(key, content)
        return f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{key}"
    except Exception:
        return None


def list_files(prefix: str = "") -> list:
    """List files in a prefix."""
    bucket = _get_bucket()
    if not bucket:
        return []

    try:
        files = []
        for obj in oss2.ObjectIterator(bucket, prefix=prefix, max_keys=50):
            files.append({"key": obj.key, "size": obj.size, "last_modified": obj.last_modified})
        return files
    except Exception:
        return []
