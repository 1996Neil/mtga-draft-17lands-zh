import hashlib
import json
import sqlite3
from unittest.mock import patch

import pytest

from src import arena_english as english


@pytest.fixture
def original(tmp_path):
    path = tmp_path / "game.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE Versions (name TEXT, value TEXT);
            INSERT INTO Versions VALUES ('Data','one');
            CREATE TABLE Cards (TitleId INT, GrpId INT);
            INSERT INTO Cards VALUES (10,100);
            CREATE TABLE Enums (LocId INT, Type TEXT);
            INSERT INTO Enums VALUES (20,'CardType'),(21,'Color'),(22,'SubType'),(30,'Phase');
            CREATE TABLE Localizations_enUS (LocId INT, Formatted INT, Loc TEXT);
            INSERT INTO Localizations_enUS VALUES
              (10,0,'Synthetic Card'),(20,0,'Creature'),(21,0,'Blue'),(22,0,'Testkind'),
              (30,0,'Not used: phase'),(90,0,'Not used: synthetic rules'),
              (91,0,'Not used: synthetic flavor');
        """)
    return path


def test_only_identity_projection_is_exported_and_source_is_unchanged(original, tmp_path):
    before = hashlib.sha256(original.read_bytes()).hexdigest()
    with english.connect_readonly(original) as db:
        result = english.prepare_index(db, tmp_path / "index.json")
        with pytest.raises(sqlite3.OperationalError):
            db.execute("DELETE FROM Cards")
    assert {r["LocId"] for r in result["localizations"]} == {10, 20, 21, 22}
    assert "Not used" not in (tmp_path / "index.json").read_text()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == before


def test_unchanged_cache_only_reads_version_metadata(original, tmp_path):
    index = tmp_path / "index.json"
    with english.connect_readonly(original) as db:
        english.prepare_index(db, index)
        english.english_localizations(db, index)
        statements = []
        db.set_trace_callback(statements.append)
        with patch.object(english, "validate_rows", side_effect=AssertionError("full revalidation")):
            english.english_localizations(db, index)
    assert statements == ["SELECT * FROM Versions"]


def test_patched_game_uses_local_index_and_missing_index_is_explicit(original, tmp_path):
    index = tmp_path / "index.json"
    with english.connect_readonly(original) as db:
        english.prepare_index(db, index)
    with sqlite3.connect(original) as db:
        db.execute("UPDATE Localizations_enUS SET Loc='中文名' WHERE LocId=10")
    with english.connect_readonly(original) as db:
        assert english.english_localizations(db, index)[0]["Loc"] == "Synthetic Card"
        with pytest.raises(ValueError, match="Prepare a local English identity index"):
            english.english_localizations(db, tmp_path / "missing.json")


def test_changed_game_version_does_not_reuse_an_old_local_index(original, tmp_path):
    index = tmp_path / "index.json"
    with english.connect_readonly(original) as db:
        english.prepare_index(db, index)
    before = index.read_bytes()
    with sqlite3.connect(original) as db:
        db.execute("UPDATE Versions SET value='two'")
        db.execute("UPDATE Localizations_enUS SET Loc='中文名' WHERE LocId=10")
    with english.connect_readonly(original) as db:
        with pytest.raises(ValueError, match="identities changed"):
            english.english_localizations(db, index)
    assert index.read_bytes() == before


def test_first_use_prepares_local_index_once(original, tmp_path, monkeypatch):
    monkeypatch.setattr(english.constants, "BASE_DIR", str(tmp_path))
    with english.connect_readonly(original) as db:
        english.english_localizations(db)
        cache = tmp_path / "Names/english-index.json"
        before = cache.read_bytes()
        with patch.object(english, "required_localizations", side_effect=AssertionError("table reread")):
            english.english_localizations(db)
    assert cache.read_bytes() == before


def test_missing_placeholder_names_do_not_block_usable_english_data(original, tmp_path):
    with sqlite3.connect(original) as db:
        db.execute("DELETE FROM Localizations_enUS WHERE LocId=22")
    output = tmp_path / "index.json"
    with english.connect_readonly(original) as db:
        payload = english.prepare_index(db, output)
        assert {row["LocId"] for row in payload["localizations"]} == {10, 20, 21}
        assert len(english.english_localizations(db, output)) == 3


def test_cache_write_failure_keeps_valid_english_input(original, tmp_path, monkeypatch):
    monkeypatch.setattr(english.constants, "BASE_DIR", str(tmp_path))
    with english.connect_readonly(original) as db:
        with patch.object(english, "prepare_index", side_effect=PermissionError("read-only")):
            assert len(english.english_localizations(db)) == 4


def test_corrupt_index_and_oversized_index_are_rejected(original, tmp_path):
    output = tmp_path / "index.json"
    with english.connect_readonly(original) as db:
        payload = english.prepare_index(db, output)
        payload["localizations"][0]["Loc"] = "Changed"
        output.write_text(json.dumps(payload))
        with pytest.raises(ValueError, match="corrupt"):
            english.english_localizations(db, output)
        with pytest.raises(ValueError, match="size budget"):
            english._load_index(str(output), 1, english.MAX_INDEX_BYTES + 1, "unused")
