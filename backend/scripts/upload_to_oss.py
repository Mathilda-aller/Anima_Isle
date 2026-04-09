import argparse
import os
import sys
from pathlib import Path
from urllib.parse import quote, urlparse

import oss2
from dotenv import load_dotenv


CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
DEFAULT_WINDOWS_SOURCE_ROOT = r"D:\yanyu dataset\v1.0 言屿图片素材\v1.0 言屿图片素材"
DEFAULT_WSL_SOURCE_ROOT = "/mnt/d/yanyu dataset/v1.0 言屿图片素材/v1.0 言屿图片素材"
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def load_env() -> None:
    load_dotenv(ROOT_DIR / ".env")


def get_env(name: str, *fallback_names: str) -> str:
    for key in (name, *fallback_names):
        value = os.getenv(key)
        if value and value.strip():
            return value.strip()
    return ""


def resolve_source_root(explicit_path: str | None) -> Path:
    candidates = [
        explicit_path,
        os.getenv("OSS_UPLOAD_SOURCE_ROOT"),
        os.getenv("IMAGE_LIBRARY_ROOT"),
        DEFAULT_WINDOWS_SOURCE_ROOT,
        DEFAULT_WSL_SOURCE_ROOT,
    ]

    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.exists():
            return path

    raise FileNotFoundError(
        "No valid source root found. Set --source-root, OSS_UPLOAD_SOURCE_ROOT, or IMAGE_LIBRARY_ROOT."
    )


def normalize_endpoint(endpoint: str) -> str:
    if not endpoint:
        raise ValueError("Missing OSS endpoint in .env")
    parsed = urlparse(endpoint if "://" in endpoint else f"https://{endpoint}")
    host = parsed.netloc or parsed.path
    if not host:
        raise ValueError(f"Invalid OSS endpoint: {endpoint}")
    return host


def build_public_url(bucket_name: str, endpoint_host: str, object_key: str) -> str:
    return f"https://{bucket_name}.{endpoint_host}/{quote(object_key, safe='/')}"


def iter_files(source_root: Path) -> list[Path]:
    return sorted(
        path
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def fetch_existing_keys(bucket: oss2.Bucket, prefix: str) -> set[str]:
    existing_keys: set[str] = set()
    marker = ""

    while True:
        result = bucket.list_objects(prefix=prefix, marker=marker, max_keys=1000)
        for obj in result.object_list:
            existing_keys.add(obj.key)

        if not result.is_truncated:
            break
        marker = result.next_marker

    return existing_keys


def upload_directory(
    source_root: Path,
    bucket_name: str,
    endpoint_host: str,
    access_key_id: str,
    access_key_secret: str,
    prefix: str,
    skip_existing: bool,
    connect_timeout: int,
) -> None:
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(
        auth,
        f"https://{endpoint_host}",
        bucket_name,
        connect_timeout=connect_timeout,
    )

    files = iter_files(source_root)
    if not files:
        print(f"No image files found under {source_root}")
        return

    clean_prefix = prefix.strip("/").replace("\\", "/")
    uploaded = 0
    skipped = 0
    existing_keys = fetch_existing_keys(bucket, clean_prefix) if skip_existing else set()

    print(f"Source root: {source_root}")
    print(f"Bucket: {bucket_name}")
    print(f"Endpoint: {endpoint_host}")
    print(f"Files to inspect: {len(files)}")
    if skip_existing:
        print(f"Existing objects detected: {len(existing_keys)}")

    for index, file_path in enumerate(files, start=1):
        relative_key = file_path.relative_to(source_root).as_posix()
        object_key = f"{clean_prefix}/{relative_key}" if clean_prefix else relative_key

        if skip_existing and object_key in existing_keys:
            skipped += 1
            print(f"[{index}/{len(files)}] skip {object_key}")
            continue

        bucket.put_object_from_file(object_key, str(file_path))
        uploaded += 1
        print(f"[{index}/{len(files)}] upload {object_key}")
        print(f"  key: {object_key}")
        print(f"  url: {build_public_url(bucket_name, endpoint_host, object_key)}")

    print(f"Upload finished. uploaded={uploaded}, skipped={skipped}, total={len(files)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload local image library to Aliyun OSS.")
    parser.add_argument("--source-root", help="Local image library root directory.")
    parser.add_argument("--prefix", default=os.getenv("OSS_OBJECT_PREFIX", ""), help="Optional OSS object key prefix.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite remote files even if the object key already exists.",
    )
    return parser.parse_args()


def main() -> int:
    load_env()
    args = parse_args()

    access_key_id = get_env("AccessKey_ID", "OSS_ACCESS_KEY_ID")
    access_key_secret = get_env("AccessKey_Secret", "OSS_ACCESS_KEY_SECRET")
    bucket_name = get_env("OSS_BUCKET_NAME", "OSS_BUCKET")
    endpoint_host = normalize_endpoint(get_env("OSS_ENDPOINT"))
    connect_timeout = int(get_env("OSS_CONNECT_TIMEOUT") or "300")

    if not access_key_id or not access_key_secret:
        raise ValueError("Missing AccessKey_ID or AccessKey_Secret in .env")
    if not bucket_name:
        raise ValueError("Missing OSS_BUCKET_NAME or OSS_BUCKET in .env")

    source_root = resolve_source_root(args.source_root)
    upload_directory(
        source_root=source_root,
        bucket_name=bucket_name,
        endpoint_host=endpoint_host,
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        prefix=args.prefix,
        skip_existing=not args.overwrite,
        connect_timeout=connect_timeout,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Upload cancelled by user.")
        raise SystemExit(130)
    except Exception as exc:
        print(f"Upload failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
