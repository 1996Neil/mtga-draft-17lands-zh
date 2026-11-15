"""A changed/localized game must not be reported as a login problem."""
import hashlib
import sqlite3
from unittest.mock import MagicMock, patch

from src import arena_english as english
from src.file_extractor import FileExtractor
from src import i18n
from src.i18n import ZH
from src.ui.windows.download import DownloadWindow


def test_identity_failure_reaches_download_without_overwriting_cache(tmp_path, monkeypatch):
    database = tmp_path / "cards.mtga"
    with sqlite3.connect(database) as db:
        db.executescript("""
            CREATE TABLE Versions (name TEXT, value TEXT);
            INSERT INTO Versions VALUES ('Data','old-version');
            CREATE TABLE Cards (TitleId INT);
            INSERT INTO Cards VALUES (1);
            CREATE TABLE Enums (LocId INT, Type TEXT);
            CREATE TABLE Localizations_enUS (LocId INT, Formatted INT, Loc TEXT);
            INSERT INTO Localizations_enUS VALUES (1,0,'Synthetic Card');
        """)
    monkeypatch.setattr(english.constants, "BASE_DIR", str(tmp_path))
    index = tmp_path / "Names/english-index.json"
    with english.connect_readonly(database) as db:
        english.prepare_index(db, index)
    previous_index = index.read_bytes()
    with sqlite3.connect(database) as db:
        db.execute("UPDATE Versions SET value='new-version'")
        db.execute("UPDATE Localizations_enUS SET Loc='中文卡名'")
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    extractor = FileExtractor("", None, None, None)
    with patch("src.file_extractor.search_local_files", return_value=[str(database)]):
        success, message, size = extractor.download_card_data(0)
    assert not success and size == 0
    assert message == english.ENGLISH_INDEX_REQUIRED
    assert "Log in" not in message
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    assert index.read_bytes() == previous_index
    assert "同一游戏版本" in ZH[message]


def test_local_database_error_is_cleared_before_a_retry(tmp_path):
    extractor = FileExtractor("", None, None, None)
    extractor._local_database_error = english.ENGLISH_INDEX_REQUIRED
    with patch("src.file_extractor.connect_readonly", side_effect=OSError("unavailable")):
        assert not extractor._retrieve_local_database(tmp_path / "missing.mtga")[0]
    assert extractor._local_database_error == ""


def test_download_error_dialog_translates_identity_guidance():
    panel = MagicMock()
    previous_language = i18n._enabled
    try:
        i18n.set_language(True)
        with patch("src.ui.windows.download.messagebox.showerror") as showerror:
            DownloadWindow._handle_error(panel, english.ENGLISH_INDEX_REQUIRED)
        showerror.assert_called_once_with(ZH["Download Error"], ZH[english.ENGLISH_INDEX_REQUIRED])
        panel.vars["status"].set.assert_called_once_with(ZH["DOWNLOAD FAILED"])
    finally:
        i18n.set_language(previous_language)
