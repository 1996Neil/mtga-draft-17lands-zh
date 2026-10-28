"""Read-only English localization input, separate from Chinese display data.

A localized enUS table must never become algorithm input. A bundled pristine
English snapshot can be used only when all non-localization identity tables
match the live database exactly. No game files or maintainer state are written.
"""
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from src import constants


VERIFIED_LOCALIZATIONS_SHA256 = "bdf0b0583d86c48a54f1a040fbdd2daaf5ad1048bd97e3b164cb701ed3ebfc3d"


def connect_readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True,
                           timeout=5)


def identity_signature(connection):
    digest = hashlib.sha256()
    for table in ("Versions", "Cards", "Enums"):
        rows = [tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')]
        # Order-independent, includes every structural field rather than names.
        digest.update(table.encode())
        for row in sorted(json.dumps(row, ensure_ascii=True) for row in rows):
            digest.update(row.encode())
            digest.update(b"\n")
    return digest.hexdigest()


def english_localizations(connection, resource=None):
    rows = [dict(row) if isinstance(row, (dict, sqlite3.Row)) else
            dict(zip(("LocId", "Formatted", "Loc"), tuple(row)))
            for row in connection.cursor().execute(constants.LOCAL_DATABASE_LOCALIZATION_QUERY)]
    if not any(re.search(r"[\u3400-\u9fff]", str(row["Loc"])) for row in rows):
        return rows
    # Card titles and enums are the fields used by the original reader. Refuse
    # Chinese or bilingual text even when the table is labelled enUS.
    used = {row[0] for row in connection.execute("SELECT TitleId FROM Cards")}
    used.update(row[0] for row in connection.execute("SELECT LocId FROM Enums"))
    localized = any(row["LocId"] in used and
                    re.search(r"[\u3400-\u9fff]", str(row["Loc"])) for row in rows)
    if not localized:
        return rows
    path = Path(resource or (Path(constants.RESOURCE_DIR) / "resources/arena/english.json"))
    if not path.is_file():
        raise ValueError("Local Arena English fields contain Chinese; verified English source is missing.")
    snapshot = json.loads(path.read_text())
    payload = snapshot.get("localizations", [])
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()
    if snapshot.get("schema") != 1 or digest != snapshot.get("localizations_sha256") or (resource is None and digest != VERIFIED_LOCALIZATIONS_SHA256):
        raise ValueError("Verified English localization snapshot is corrupt.")
    if identity_signature(connection) != snapshot.get("identity_sha256"):
        raise ValueError("Arena data version/identities changed; verified English source does not match. Previous dataset kept.")
    if any(re.search(r"[\u3400-\u9fff]", str(row["Loc"]))
           for row in payload if row["LocId"] in used):
        raise ValueError("Verified English source contains localized algorithm fields.")
    return payload
