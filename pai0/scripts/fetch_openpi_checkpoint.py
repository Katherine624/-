#!/usr/bin/env python3
"""Fetch the official public pi0_libero checkpoint from GCS without gsutil.

Files are saved directly under --dest (for example, --dest
/root/autodl-tmp/openpi-assets/checkpoints/pi0_libero). Interrupted downloads
are resumed from .part files. The manifest size and MD5 of every object are
checked before a file is accepted. This is a *published* checkpoint, not one
trained by this reproduction project.
"""

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


BUCKET = "openpi-assets"
PREFIX = "checkpoints/pi0_libero/"
EXPECTED_COUNT = 19
EXPECTED_BYTES = 12_014_131_888
CHUNK_SIZE = 4 * 1024 * 1024


def log(message):
    print(message, flush=True)


def retry_delay(attempt):
    return min(2 ** (attempt - 1), 30)


def list_objects(retries, timeout):
    objects = []
    page_token = None
    while True:
        query = {
            "prefix": PREFIX,
            "maxResults": "1000",
            "fields": "nextPageToken,items(name,size,md5Hash)",
        }
        if page_token:
            query["pageToken"] = page_token
        url = f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o?{urlencode(query)}"
        for attempt in range(1, retries + 1):
            try:
                with urlopen(Request(url, headers={"Accept-Encoding": "identity"}), timeout=timeout) as response:
                    page = json.load(response)
                break
            except (OSError, URLError, ValueError) as exc:
                if attempt == retries:
                    raise RuntimeError(f"GCS object listing failed after {retries} attempts: {exc}") from exc
                time.sleep(retry_delay(attempt))
        objects.extend(page.get("items", []))
        page_token = page.get("nextPageToken")
        if not page_token:
            break
    if len(objects) != EXPECTED_COUNT or sum(int(item["size"]) for item in objects) != EXPECTED_BYTES:
        raise RuntimeError(
            "Published checkpoint object list changed; refusing an unpinned download: "
            f"{len(objects)} objects, {sum(int(item['size']) for item in objects)} bytes "
            f"(expected {EXPECTED_COUNT}, {EXPECTED_BYTES})."
        )
    return objects


def destination(root, object_name):
    if not object_name.startswith(PREFIX):
        raise ValueError(f"Object outside expected prefix: {object_name!r}")
    suffix = object_name[len(PREFIX):]
    parts = suffix.split("/")
    if not suffix or any(part in ("", ".", "..") or "\\" in part or ":" in part for part in parts):
        raise ValueError(f"Unsafe object path: {object_name!r}")
    path = root.joinpath(*parts)
    # The components above exclude traversal. Keep this check lexical: resolving
    # paths while sibling threads create directories can be inconsistent on Windows.
    if not path.is_relative_to(root):
        raise ValueError(f"Object path escapes --dest: {object_name!r}")
    return path


def md5_matches(path, encoded_digest):
    expected = base64.b64decode(encoded_digest, validate=True)
    digest = hashlib.md5()  # GCS publishes MD5 for these objects; not used for security.
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.digest() == expected


def download_one(root, item, retries, timeout):
    name = item["name"]
    size = int(item["size"])
    digest = item.get("md5Hash")
    if not digest:
        raise RuntimeError(f"Missing GCS MD5 for {name}")
    target = destination(root, name)
    part = target.with_name(target.name + ".part")
    if not part.is_relative_to(root):
        raise ValueError(f"Unsafe partial-file path: {part}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size == size and md5_matches(target, digest):
        log(f"SKIP {name} ({size} bytes, MD5 verified)")
        return
    if target.exists():
        log(f"REPLACE {name}: existing file has wrong size or MD5")
    if part.is_symlink() or target.is_symlink():
        raise RuntimeError(f"Refusing symlink at {part} or {target}")
    url = f"https://storage.googleapis.com/{BUCKET}/{quote(name, safe='/')}"
    for attempt in range(1, retries + 1):
        try:
            offset = part.stat().st_size if part.is_file() else 0
            if offset > size:
                part.unlink()
                offset = 0
            if offset < size:
                headers = {"Accept-Encoding": "identity"}
                if offset:
                    headers["Range"] = f"bytes={offset}-"
                with urlopen(Request(url, headers=headers), timeout=timeout) as response:
                    status = response.status
                    if offset and status == 206:
                        match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
                        if not match or int(match.group(1)) != offset or int(match.group(3)) != size:
                            raise RuntimeError(f"Invalid Content-Range for {name}: {response.headers.get('Content-Range')}")
                        mode = "ab"
                    elif status == 200:
                        mode = "wb"  # The server ignored Range; restart this object safely.
                    else:
                        raise RuntimeError(f"Unexpected HTTP {status} for {name}")
                    log(f"GET {name} from byte {offset if mode == 'ab' else 0} (attempt {attempt}/{retries})")
                    with part.open(mode) as output:
                        while True:
                            chunk = response.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            output.write(chunk)
            actual = part.stat().st_size
            if actual != size:
                raise IOError(f"Incomplete {name}: {actual}/{size} bytes")
            if not md5_matches(part, digest):
                part.unlink()
                raise IOError(f"MD5 mismatch for {name}; partial file removed")
            os.replace(part, target)
            log(f"OK {name} ({size} bytes, MD5 verified)")
            return
        except (OSError, URLError, RuntimeError, ValueError) as exc:
            if attempt == retries:
                raise RuntimeError(f"Failed to download {name} after {retries} attempts: {exc}") from exc
            log(f"RETRY {name}: {exc}")
            time.sleep(retry_delay(attempt))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, help="Directory to contain params/ and assets/")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent downloads (default: 4)")
    parser.add_argument("--retries", type=int, default=6, help="Attempts per object (default: 6)")
    parser.add_argument("--timeout", type=int, default=90, help="HTTP read timeout in seconds (default: 90)")
    parser.add_argument("--list-only", action="store_true", help="Check public object listing without downloading")
    args = parser.parse_args()
    if not args.list_only and args.dest is None:
        parser.error("--dest is required unless --list-only is used")
    if not 1 <= args.workers <= 8 or args.retries < 1 or args.timeout < 1:
        parser.error("--workers must be 1..8; --retries and --timeout must be positive")
    objects = list_objects(args.retries, args.timeout)
    log(f"Official published pi0_libero: {len(objects)} objects, {EXPECTED_BYTES / 1024**3:.3f} GiB")
    if args.list_only:
        for item in objects:
            log(f"{item['size']:>12}  {item['name']}")
        return
    root = args.dest.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    targets = [destination(root, item["name"]) for item in objects]
    if len(set(targets)) != len(targets):
        raise RuntimeError("Duplicate checkpoint object paths")
    remaining = sum(int(item["size"]) for item, path in zip(objects, targets) if not path.is_file() or path.stat().st_size != int(item["size"]))
    free = shutil.disk_usage(root).free
    if free < remaining + 1024**3:
        raise RuntimeError(f"Insufficient free disk: {free / 1024**3:.2f} GiB; need at least {(remaining + 1024**3) / 1024**3:.2f} GiB")
    log(f"Destination: {root} | free disk: {free / 1024**3:.2f} GiB")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download_one, root, item, args.retries, args.timeout): item["name"] for item in objects}
        failures = []
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                failures.append(str(exc))
                log(f"ERROR {futures[future]}: {exc}")
    if failures:
        raise RuntimeError(f"{len(failures)} object(s) failed; re-run the same command to resume")
    log(f"COMPLETE: {len(objects)} verified objects in {root}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
