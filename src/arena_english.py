"""Local English identities; no redistributed game text dump.

Only titles and Color/CardType/SubType names are read. A patched game requires
an index prepared locally from an unmodified database of the same version.
Unchanged index files are validated once per process, not once per card/poll.
"""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

from src import constants

MAX_INDEX_BYTES = 4 * 1024 * 1024
REQUIRED_IDS = """
    SELECT TitleId AS id FROM Cards WHERE TitleId > 0
    UNION SELECT LocId FROM Enums WHERE Type IN ('Color','CardType','SubType')
"""

ENGLISH_INDEX_REQUIRED = (
    "Arena identities changed or English names were localized. "
    "Prepare a local English identity index from an unmodified database "
    "of the same game version using Tools/prepare_english_index.py. "
    "Existing datasets are kept."
)


class EnglishIdentityError(ValueError):
    """The installed game needs a matching local English identity index."""


def connect_readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, timeout=5)


def identity_signature(connection):
    """A small version key; never hash full Cards/localization tables."""
    versions = sorted(tuple(row) for row in connection.execute("SELECT * FROM Versions"))
    if not versions:
        raise ValueError("Arena database has no version metadata")
    return hashlib.sha256(json.dumps(versions, ensure_ascii=True).encode()).hexdigest()


def required_localizations(connection):
    query = constants.LOCAL_DATABASE_LOCALIZATION_QUERY + f" WHERE A.LocId IN ({REQUIRED_IDS})"
    return [dict(row) if isinstance(row, (dict, sqlite3.Row)) else
            dict(zip(("LocId", "Formatted", "Loc"), tuple(row)))
            for row in connection.execute(query)]


def validate_rows(rows):
    if not isinstance(rows, list) or not 0 < len(rows) <= 100000:
        raise ValueError("Invalid English identity rows")
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {"LocId", "Formatted", "Loc"} or
                type(row["LocId"]) is not int or row["LocId"] <= 0 or row["LocId"] in seen or
                type(row["Formatted"]) is not int or not isinstance(row["Loc"], str) or
                not row["Loc"] or len(row["Loc"]) > 1024 or
                re.search(r"[\u3400-\u9fff<>\x00-\x08]", row["Loc"])):
            raise ValueError("English identity index is corrupt or contains localized text")
        seen.add(row["LocId"])
    return rows


def payload_digest(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()


def prepare_index(connection, output):
    """Explicit/local preparation only; never modify the source database."""
    output = Path(output)
    if output.suffix != ".json":
        raise ValueError("The local identity index must be a JSON file")
    rows = validate_rows(required_localizations(connection))
    payload = {"schema": 2, "version_key": identity_signature(connection),
               "rows_sha256": payload_digest(rows), "localizations": rows}
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    if len(data) > MAX_INDEX_BYTES:
        raise ValueError("English identity index exceeds its size budget")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="english-index-", dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return payload


@lru_cache(maxsize=2)
def _load_index(path, modified_ns, size, version_key):
    if size > MAX_INDEX_BYTES:
        raise ValueError("English identity index exceeds its size budget")
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != 2:
        raise ValueError("English identity index is corrupt or uses an unsupported schema")
    if payload.get("version_key") != version_key:
        raise ValueError("Arena identities changed; prepare an index from this game's original English data")
    rows = validate_rows(payload.get("localizations"))
    if payload_digest(rows) != payload.get("rows_sha256"):
        raise ValueError("English identity index is corrupt")
    return rows


def english_localizations(connection, resource=None):
    path = Path(resource) if resource is not None else (
        Path(constants.BASE_DIR) / "Names/english-index.json")
    version_key = identity_signature(connection)
    if path.is_file():
        stat = path.stat()
        try:
            return _load_index(str(path.resolve()), stat.st_mtime_ns, stat.st_size, version_key)
        except ValueError as error:
            if "identities changed" not in str(error):
                raise
    rows = required_localizations(connection)
    if any(re.search(r"[\u3400-\u9fff]", row["Loc"]) for row in rows):
        raise EnglishIdentityError(ENGLISH_INDEX_REQUIRED)
    validate_rows(rows)
    if resource is None:
        try:
            prepare_index(connection, path)
            stat = path.stat()
            return _load_index(str(path.resolve()), stat.st_mtime_ns, stat.st_size, version_key)
        except OSError:
            # A read-only/full profile must not break an otherwise usable game.
            return rows
    return rows
