"""One-shot, version-driven Chinese name updates; no polling or full rescan.

The bundled snapshot seeds a small SQLite store once. Unchanged startups read
one metadata row and one <=32 KiB remote manifest. Only changed rows are checked
and written in a single transaction. Network failure keeps the working version.
"""
import gzip
from contextlib import contextmanager
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import threading
import time
import urllib.request

BASE_URL = "https://raw.githubusercontent.com/1996Neil/mtga-card-names/main/updates/"
APP_ID = 0x4E414D45
FIELDS = {"arena_id", "english", "chinese", "set_code", "primary", "face_type", "source", "status"}
TRUSTED = {"static-verified-client-pending", "native-regression-passed;unsampled-cards-static-only"}
VERSION = re.compile(r"([0-9]{4})\.([0-9]{1,3})\.([0-9]{1,3})-r([1-9][0-9]{0,4})")
SHA = re.compile(r"[0-9a-f]{64}")
_FLIGHT = threading.Lock()


@contextmanager
def connection(path, **kwargs):
    db = sqlite3.connect(path, timeout=0.3, **kwargs)
    try:
        with db:
            yield db
    finally:
        db.close()


def version_key(value):
    if not isinstance(value, str) or not (match := VERSION.fullmatch(value)):
        raise ValueError("Invalid names version")
    return tuple(map(int, match.groups()))


def validate_row(row):
    if not isinstance(row, dict) or set(row) != FIELDS:
        raise ValueError("Unexpected name fields")
    aid = row["arena_id"]
    if not isinstance(aid, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", aid):
        raise ValueError("Invalid card identity")
    for key in ("english", "chinese", "set_code", "source", "status"):
        text = row[key]
        if not isinstance(text, str) or not text or len(text) > 1024 or re.search(r"[\x00-\x1f<>]", text):
            raise ValueError("Invalid plain name")
    if (not re.search(r"[\u3400-\u9fff]", row["chinese"]) or
            row["status"] not in TRUSTED or type(row["primary"]) is not int or
            row["primary"] not in (0, 1) or type(row["face_type"]) is not int or
            not 0 <= row["face_type"] <= 100):
        raise ValueError("Untrusted name identity")
    return aid, json.dumps(row, ensure_ascii=False, separators=(",", ":"))


def store_version(path):
    with connection(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        if db.execute("PRAGMA application_id").fetchone()[0] != APP_ID:
            raise ValueError("Not an automatic names store")
        return db.execute("SELECT version, rows FROM metadata WHERE id=1").fetchone()


def seed_store(path, bundled, pin):
    """Only read/validate all bundled names on first install or new baseline."""
    version_key(pin["data_version"])
    if path.exists():
        current = store_version(path)
        if current and version_key(current[0]) >= version_key(pin["data_version"]):
            return current
    payload = json.loads(bundled.read_text(encoding="utf-8"))
    if (payload.get("schema") != 1 or payload.get("data_version") != pin["data_version"] or
            payload.get("source_sha256") != pin["cards_jsonl_sha256"] or
            len(payload["cards"]) != pin["rows"]):
        raise ValueError("Bundled names do not match their pinned version")
    rows = [validate_row(row) for row in payload["cards"]]
    if len({aid for aid, _ in rows}) != len(rows):
        raise ValueError("Duplicate bundled name")
    path.parent.mkdir(parents=True, exist_ok=True)
    with connection(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute(f"PRAGMA application_id={APP_ID}")
        db.execute("CREATE TABLE IF NOT EXISTS metadata(id INTEGER PRIMARY KEY CHECK(id=1), version TEXT, rows INTEGER)")
        db.execute("CREATE TABLE IF NOT EXISTS names(id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        current = db.execute("SELECT version, rows FROM metadata WHERE id=1").fetchone()
        if current and version_key(current[0]) >= version_key(pin["data_version"]):
            return current  # Another process seeded/updated while we read the bundle.
        db.execute("DELETE FROM names")
        db.executemany("INSERT INTO names VALUES (?, ?)", rows)
        db.execute("INSERT OR REPLACE INTO metadata VALUES (1, ?, ?)", (pin["data_version"], len(rows)))
    return pin["data_version"], len(rows)


def fetch(relative, limit, timeout=3):
    # Every URL is constructed from a fixed publisher and a strict relative path.
    if relative != "latest.json" and not re.fullmatch(r"patches/[0-9a-f]{64}\.json\.gz", relative):
        raise ValueError("Invalid update path")
    request = urllib.request.Request(BASE_URL + relative, headers={"User-Agent": "mtga-zh-names/1"})
    deadline = time.monotonic() + timeout
    with urllib.request.urlopen(request, timeout=timeout) as response:
        parts, size = [], 0
        while size <= limit:
            if time.monotonic() >= deadline:
                raise TimeoutError("Name request time budget exhausted")
            block = response.read1(min(65536, limit + 1 - size))
            if not block:
                break
            parts.append(block)
            size += len(block)
        raw = b"".join(parts)
    if len(raw) > limit:
        raise ValueError("Name update exceeds download limit")
    return raw


def plan_updates(index, current):
    if (not isinstance(index, dict) or index.get("schema") != 1 or
            type(index.get("rows")) is not int or not 0 < index["rows"] <= 100000):
        raise ValueError("Invalid version manifest")
    target = index.get("version")
    if version_key(target) <= version_key(current):
        return []  # Never downgrade, even if a CDN briefly serves old metadata.
    edges = index.get("patches")
    if not isinstance(edges, list) or len(edges) > 64:
        raise ValueError("Invalid update chain")
    path = []
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("Invalid update edge")
        if edge.get("from") != current:
            continue
        new = edge.get("to")
        if version_key(new) <= version_key(current) or version_key(new) > version_key(target):
            raise ValueError("Non-forward update")
        sha = edge.get("sha256")
        if (not isinstance(sha, str) or not SHA.fullmatch(sha) or
                edge.get("file") != f"patches/{sha}.json.gz" or
                type(edge.get("bytes")) is not int or not 0 < edge["bytes"] <= 2 * 1024 * 1024 or
                any(type(edge.get(k)) is not int or not 0 <= edge[k] <= 100000 for k in ("rows", "upserts", "removes"))):
            raise ValueError("Invalid patch metadata")
        path.append(edge)
        current = new
    if current != target or not path or path[-1]["rows"] != index["rows"]:
        raise ValueError("No incremental path; keeping the installed baseline")
    if sum(edge["bytes"] for edge in path) > 4 * 1024 * 1024:
        raise ValueError("Update exceeds this startup's byte budget")
    return path


def apply_patch(db, edge, compressed):
    if len(compressed) != edge["bytes"] or hashlib.sha256(compressed).hexdigest() != edge["sha256"]:
        raise ValueError("New patch hash mismatch")
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("Expanded patch too large")
    patch = json.loads(raw)
    if (not isinstance(patch, dict) or set(patch) != {"schema", "from", "to", "rows", "upserts", "removes"} or
            patch["schema"] != 1 or any(patch[k] != edge[k] for k in ("from", "to", "rows")) or
            not isinstance(patch["upserts"], list) or not isinstance(patch["removes"], list) or
            len(patch["upserts"]) != edge["upserts"] or len(patch["removes"]) != edge["removes"]):
        raise ValueError("Patch differs from version metadata")
    rows = [validate_row(row) for row in patch["upserts"]]
    removed = patch["removes"]
    ids = [aid for aid, _ in rows] + removed
    if (any(not isinstance(aid, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", aid) for aid in removed) or
            len(ids) != len(set(ids))):
        raise ValueError("Duplicate/invalid changed identities")
    current, count = db.execute("SELECT version, rows FROM metadata WHERE id=1").fetchone()
    if current != edge["from"]:
        raise ValueError("Incremental baseline changed")
    # Point lookups only: unchanged rows are neither scanned nor verified.
    added = sum(not db.execute("SELECT 1 FROM names WHERE id=?", (aid,)).fetchone() for aid, _ in rows)
    for aid in removed:
        if db.execute("DELETE FROM names WHERE id=?", (aid,)).rowcount != 1:
            raise ValueError("Removal missing from installed version")
    if count + added - len(removed) != edge["rows"]:
        raise ValueError("Incremental row count mismatch")
    db.executemany("INSERT OR REPLACE INTO names VALUES (?, ?)", rows)
    db.execute("UPDATE metadata SET version=?, rows=? WHERE id=1", (edge["to"], edge["rows"]))
    return len(rows) + len(removed)


def check_once(path, bundled, pin, download=fetch):
    """Exactly one manifest request; no retries, timers, full-download fallback."""
    if not _FLIGHT.acquire(blocking=False):
        return {"status": "busy"}
    try:
        current, rows = seed_store(path, bundled, pin)
        index = json.loads(download("latest.json", 32768))
        edges = plan_updates(index, current)
        if not edges:
            return {"status": "current", "version": current, "rows": rows, "changed": 0}
        deadline = time.monotonic() + 12
        payloads = []
        for edge in edges:
            if time.monotonic() >= deadline:
                raise TimeoutError("Name update time budget exhausted")
            payloads.append(download(edge["file"], edge["bytes"]))
        with connection(path) as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT version FROM metadata WHERE id=1").fetchone()[0] != current:
                return {"status": "busy"}
            changed = sum(apply_patch(db, edge, raw) for edge, raw in zip(edges, payloads))
        return {"status": "updated", "version": index["version"], "rows": index["rows"], "changed": changed}
    finally:
        _FLIGHT.release()
