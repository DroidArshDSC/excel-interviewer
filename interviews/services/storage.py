# interviews/services/storage.py
import os, requests, mimetypes, time
from urllib.parse import quote_plus

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET", "submissions")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")

def upload_bytes_to_supabase(file_bytes: bytes, dest_path: str, content_type: str) -> str:
    """
    Uploads bytes to Supabase Storage at /storage/v1/object/{bucket}/{path}
    Returns public URL (if bucket public) or path to the object.
    Note: for private buckets you'll need to generate a signed URL separately.
    """
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{quote_plus(dest_path)}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
        "Content-Type": content_type,
    }
    resp = requests.put(url, data=file_bytes, headers=headers, timeout=60)
    resp.raise_for_status()
    # Return public URL path for public bucket
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{dest_path}"
    return public_url

def generate_signed_url(object_path: str, expires_in: int = 60) -> str:
    """
    Generate a temporary signed URL for a stored object (server-side).
    Uses Supabase Storage API: /object/sign/{bucket}/{path}
    """
    url = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET}/{quote_plus(object_path)}?expires_in={int(expires_in)}"
    headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # response: {"signedURL":"https://..."}
    return data.get("signedURL") or data.get("signed_url")
