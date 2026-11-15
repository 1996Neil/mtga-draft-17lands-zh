"""Synthetic regressions for a restarted game with multiple active courses."""
import json
from unittest.mock import MagicMock

from src.log_scanner import ArenaScanner


def scanner_for(tmp_path, monkeypatch, courses):
    from src import constants
    monkeypatch.setattr(constants, "TEMP_FOLDER", str(tmp_path))
    log = tmp_path / "Player.log"
    log.write_text(json.dumps({"Courses": courses}, separators=(",", ":")) + "\n")
    sets = MagicMock()
    sets.data = {}
    sets.events = []
    return ArenaScanner(str(log), sets, retrieve_unknown=False)


def test_restart_finds_draft_after_constructed_course_and_uses_its_pool(tmp_path, monkeypatch):
    scanner = scanner_for(tmp_path, monkeypatch, [
        {"InternalEventName": "Alchemy_Play", "CurrentModule": "Complete", "CardPool": ["wrong"]},
        {"InternalEventName": "PremierDraft_TST_20261110", "CurrentModule": "PlayerDraft", "CardPool": ["101", "102"]},
    ])
    assert scanner.draft_start_search()
    assert scanner.retrieve_current_limited_event() == ("TST", "PremierDraft")
    assert scanner.taken_cards == ["101", "102"]
    with open(scanner.state_file) as saved:
        assert json.load(saved)["taken_cards"] == ["101", "102"]
    scanner.taken_cards = []
    scanner.pool_offset = 0
    assert scanner._search_card_pool()
    assert scanner.taken_cards == ["101", "102"]


def test_completed_limited_course_does_not_replace_active_draft(tmp_path, monkeypatch):
    scanner = scanner_for(tmp_path, monkeypatch, [
        {"InternalEventName": "QuickDraft_OLD_20261001", "CurrentModule": "Complete", "CardPool": ["old"]},
        {"InternalEventName": "PremierDraft_TST_20261110", "CurrentModule": "PlayerDraft", "CardPool": []},
    ])
    assert scanner.draft_start_search()
    assert scanner.retrieve_current_limited_event() == ("TST", "PremierDraft")
    assert scanner.taken_cards == []


def test_late_pick_state_with_small_wheeled_packs_is_valid():
    state = {
        "current_pack": 3, "current_pick": 14, "number_of_players": 8,
        "pack_cards": [["one"]] * 8,
    }
    assert ArenaScanner._state_is_sane(state)
    assert not ArenaScanner._state_is_sane(dict(state, current_pick=100))


def test_existing_draft_wins_over_another_unfinished_sealed_course(tmp_path, monkeypatch):
    scanner = scanner_for(tmp_path, monkeypatch, [
        {"InternalEventName": "Sealed_OLD_20261001", "CurrentModule": "DeckSelect", "CardPool": ["old"]},
        {"InternalEventName": "PremierDraft_TST_20261110", "CurrentModule": "DeckSelect", "CardPool": ["new"]},
    ])
    scanner.event_string = "PremierDraft_TST_20261110"
    scanner.taken_cards = ["preserved"]
    assert not scanner.draft_start_search()
    assert scanner.taken_cards == ["preserved"]
    scanner.pool_offset = 0
    assert scanner._search_card_pool()
    assert scanner.taken_cards == ["new"]


def test_unbound_drafting_module_wins_over_old_deckselect(tmp_path, monkeypatch):
    scanner = scanner_for(tmp_path, monkeypatch, [
        {"InternalEventName": "Sealed_OLD_20261001", "CurrentModule": "DeckSelect", "CardPool": ["old"]},
        {"InternalEventName": "PremierDraft_TST_20261110", "CurrentModule": "PlayerDraft", "CardPool": []},
    ])
    assert scanner.draft_start_search()
    assert scanner.retrieve_current_limited_event() == ("TST", "PremierDraft")


def test_ambiguous_unbound_courses_do_not_choose_or_merge_a_pool(tmp_path, monkeypatch):
    scanner = scanner_for(tmp_path, monkeypatch, [
        {"InternalEventName": "Sealed_OLD_20261001", "CurrentModule": "DeckSelect", "CardPool": ["old"]},
        {"InternalEventName": "PremierDraft_TST_20261110", "CurrentModule": "DeckSelect", "CardPool": ["new"]},
    ])
    assert not scanner.draft_start_search()
    assert not scanner._search_card_pool()
    assert scanner.taken_cards == []
