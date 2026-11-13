#!/usr/bin/env python3
"""Sync resources/localization/cards.json from the public mtga-card-names release.

The public package is the single source of truth:
  https://github.com/1996Neil/mtga-card-names

This script is read-only with respect to game files. It verifies the pinned
manifest and asset hashes before writing the legacy 17Lands snapshot schema.

Usage:
    python3 Tools/sync_card_names.py                 # check pinned version
    python3 Tools/sync_card_names.py --apply         # download + write
    python3 Tools/sync_card_names.py --input dist/cards.jsonl --apply
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_FILE = ROOT / "resources" / "localization" / "RELEASE.json"
INDEX = ROOT / "resources" / "localization" / "cards.json"
UA = "mtga-draft-17lands-zh/sync-card-names"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_release() -> dict:
    try:
        data = json.loads(RELEASE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        sys.exit(f"[error] cannot read {RELEASE_FILE}: {exc}")
    for key in ("package", "release", "data_version", "cards_jsonl_sha256", "cards_jsonl_gz_sha256", "rows"):
        if key not in data:
            sys.exit(f"[error] {RELEASE_FILE} missing {key}")
    return data


def download(url: str, expected: str, timeout: int = 60, attempts: int = 3) -> bytes:
    last = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
            if sha256_bytes(data) != expected:
                raise ValueError(f"sha256 mismatch for {url}")
            return data
        except (OSError, ValueError, urllib.error.URLError) as exc:
            last = exc
            if attempt < attempts:
                time.sleep(1.5 * attempt)
    sys.exit(f"[error] download failed after {attempts} attempts: {url}: {last}")


def load_cards_bytes(path: Path, release: dict) -> bytes:
    data = path.read_bytes()
    if path.suffix == ".gz":
        if sha256_bytes(data) != release["cards_jsonl_gz_sha256"]:
            sys.exit(f"[error] {path} gzip sha256 does not match RELEASE.json")
        raw = gzip.decompress(data)
    else:
        raw = data
    if sha256_bytes(raw) != release["cards_jsonl_sha256"]:
        sys.exit(f"[error] {path} card JSONL sha256 does not match RELEASE.json")
    return raw


def fetch_release(release: dict) -> bytes:
    base = f"https://github.com/{release['package']}/releases/download/{release['release']}"
    manifest_bytes = download(f"{base}/manifest.json", release["manifest_sha256"])
    try:
        manifest = json.loads(manifest_bytes)
    except ValueError as exc:
        sys.exit(f"[error] invalid manifest: {exc}")
    if manifest.get("data_version") != release["data_version"]:
        sys.exit(f"[error] manifest data_version {manifest.get('data_version')!r} != {release['data_version']!r}")
    entry = (manifest.get("files") or {}).get("cards.jsonl.gz") or {}
    if entry.get("sha256") != release["cards_jsonl_gz_sha256"]:
        sys.exit("[error] manifest cards.jsonl.gz hash does not match RELEASE.json")
    gz = download(f"{base}/cards.jsonl.gz", release["cards_jsonl_gz_sha256"])
    raw = gzip.decompress(gz)
    if sha256_bytes(raw) != release["cards_jsonl_sha256"]:
        sys.exit("[error] downloaded cards.jsonl.gz does not match RELEASE.json")
    return raw


def build_payload(raw: bytes, release: dict) -> dict:
    cards = []
    seen = set()
    for line in raw.decode("utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        grp_id = str(row["grp_id"])
        if grp_id in seen:
            sys.exit(f"[error] duplicate grp_id {grp_id} in release")
        seen.add(grp_id)
        if not row.get("zh"):
            continue
        cards.append({
            "arena_id": str(row["grp_id"]),
            "english": row["en"],
            "chinese": row["zh"],
            "set_code": row["set"],
            "primary": int(row["is_primary"]),
            "face_type": int(row["face_type"]),
            "source": row["source"],
            "status": row["status"],
        })
    cards.sort(key=lambda card: int(card["arena_id"]))
    if len(cards) != release["rows"]:
        sys.exit(f"[error] expected {release['rows']} Chinese rows, got {len(cards)}")
    return {
        "schema": 1,
        "data_version": release["data_version"],
        "package": release["package"],
        "release": release["release"],
        "source_sha256": release["cards_jsonl_sha256"],
        "cards": cards,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="local cards.jsonl or cards.jsonl.gz")
    parser.add_argument("--apply", action="store_true", help="write resources/localization/cards.json")
    parser.add_argument("--check", action="store_true", help="verify the existing file against the pin")
    args = parser.parse_args()

    release = read_release()
    if args.check:
        try:
            current = json.loads(INDEX.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            sys.exit(f"[error] cannot read {INDEX}: {exc}")
        problems = []
        if current.get("data_version") != release["data_version"]:
            problems.append(f"data_version {current.get('data_version')!r} != {release['data_version']!r}")
        if current.get("source_sha256") != release["cards_jsonl_sha256"]:
            problems.append("source_sha256 mismatch")
        if len(current.get("cards") or []) != release["rows"]:
            problems.append(f"rows {len(current.get('cards') or [])} != {release['rows']}")
        if problems:
            sys.exit("[error] " + "; ".join(problems))
        print(json.dumps({"ok": True, "data_version": release["data_version"], "rows": release["rows"]}))
        return

    raw = load_cards_bytes(args.input.resolve(), release) if args.input else fetch_release(release)
    payload = build_payload(raw, release)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    print(json.dumps({
        "data_version": payload["data_version"],
        "rows": len(payload["cards"]),
        "source_sha256": payload["source_sha256"],
        "bytes": len(encoded),
        "apply": args.apply,
    }, ensure_ascii=False))

    if not args.apply:
        print("dry-run: pass --apply to write resources/localization/cards.json")
        return

    fd, tmp_name = tempfile.mkstemp(prefix="cards.json.", dir=str(INDEX.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.write(b"\n")
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, INDEX)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    print(f"wrote {INDEX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
