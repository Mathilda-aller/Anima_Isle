import base64
import hashlib
import hmac
import mimetypes
import os
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib import error, parse, request

from dotenv import load_dotenv


current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

load_dotenv(os.path.join(root_dir, ".env"))

SOURCE_ROOT = Path(
    os.getenv(
        "OSS_UPLOAD_SOURCE_ROOT",
        "/mnt/d/yanyu dataset/v1.0 言屿图片素材/v1.0 言屿图片素材",
    )
)
OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME", "anima-isle-images")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "https://oss-cn-beijing.aliyuncs.com")
ACCESS_KEY_ID = (os.getenv("AccessKey_ID") or os.getenv("OSS_ACCESS_KEY_ID") or "").strip()
ACCESS_KEY_SECRET = (os.getenv("AccessKey_Secret") or os.getenv("OSS_ACCESS_KEY_SECRET") or "").strip()


def _endpoint_host() -> str:
    parsed = parse.urlparse(OSS_ENDPOINT if "://" in OSS_ENDPOINT else f"https://{OSS_ENDPOINT}")
    return parsed.netloc or parsed.path


def _object_key(path: Path) -> str:
    return path.relative_to(SOURCE_ROOT).as_posix()


def _resource_path(object_key: str) -> str:
    return f"/{OSS_BUCKET_NAME}/{object_key}"


def _object_url(object_key: str) -> str:
    quoted = parse.quote(object_key, safe="/")
    return f"https://{OSS_BUCKET_NAME}.{_endpoint_host()}/{quoted}"


def _sign(method: str, content_type: str, date_str: str, object_key: str) -> str:
    string_to_sign = f"{method}\n\n{content_type}\n{date_str}\n{_resource_path(object_key)}"
    digest = hmac.new(
        ACCESS_KEY_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    signature = base64.b64encode(digest).decode("utf-8")
    return f"OSS {ACCESS_KEY_ID}:{signature}"


def _build_request(method: str, object_key: str, content_type: str, data: bytes | None = None) -> request.Request:
    date_str = format_datetime(datetime.now(timezone.utc), usegmt=True)
    headers = {
        "Date": date_str,
        "Authorization": _sign(method, content_type, date_str, object_key),
    }
    if content_type:
        headers["Content-Type"] = content_type
    if data is not None:
        headers["Content-Length"] = str(len(data))
    return request.Request(_object_url(object_key), data=data, headers=headers, method=method)


def _head_object(object_key: str) -> int | None:
    req = _build_request("HEAD", object_key, "")
    try:
        with request.urlopen(req) as response:
            return int(response.headers.get("Content-Length", "0"))
    except error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def _put_object(object_key: str, file_path: Path) -> None:
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    data = file_path.read_bytes()
    req = _build_request("PUT", object_key, content_type, data=data)
    with request.urlopen(req) as response:
        if response.status not in (200, 201):
            raise RuntimeError(f"Upload failed for {object_key}, status={response.status}")


def upload_all() -> None:
    if not ACCESS_KEY_ID or not ACCESS_KEY_SECRET:
        raise ValueError("Missing OSS credentials in .env")
    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"Source root not found: {SOURCE_ROOT}")

    files = sorted(path for path in SOURCE_ROOT.rglob("*") if path.is_file())
    total = len(files)
    if total == 0:
        print("No files found to upload.")
        return

    uploaded = 0
    skipped = 0
    print(f"Uploading {total} files to bucket {OSS_BUCKET_NAME} via {_endpoint_host()}")

    for index, path in enumerate(files, start=1):
        object_key = _object_key(path)
        remote_size = _head_object(object_key)
        local_size = path.stat().st_size

        if remote_size == local_size:
            skipped += 1
            print(f"[{index}/{total}] skip {object_key}")
            continue

        _put_object(object_key, path)
        uploaded += 1
        print(f"[{index}/{total}] upload {object_key}")

    print(f"Upload finished. uploaded={uploaded}, skipped={skipped}, total={total}")


if __name__ == "__main__":
    upload_all()
