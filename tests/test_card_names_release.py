"""Pinned public names-only release contract for resources/localization/cards.json."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = json.loads((ROOT / "resources/localization/RELEASE.json").read_text(encoding="utf-8"))
CARDS = json.loads((ROOT / "resources/localization/cards.json").read_text(encoding="utf-8"))
HAN = re.compile(r"[\u3400-\u9fff]")
TAG = re.compile(r"<[^>]*>")
PATH = re.compile(r"(/Users/|/home/|[A-Za-z]:\\)")


def test_release_pin_matches_index():
    assert CARDS["schema"] == 1
    assert CARDS["data_version"] == RELEASE["data_version"]
    assert CARDS["source_sha256"] == RELEASE["cards_jsonl_sha256"]
    assert len(CARDS["cards"]) == RELEASE["rows"]


def test_rows_are_unique_plain_and_trusted():
    ids = set()
    trusted = {"static-verified-client-pending", "native-regression-passed;unsampled-cards-static-only"}
    for row in CARDS["cards"]:
        assert row["arena_id"] not in ids
        ids.add(row["arena_id"])
        assert row["english"] and row["chinese"]
        assert HAN.search(row["chinese"])
        assert row["chinese"] != row["english"]
        assert not TAG.search(row["chinese"]) and not TAG.search(row["english"])
        assert not PATH.search(row["chinese"]) and not PATH.search(row["english"])
        assert row["status"] in trusted
        assert isinstance(row["primary"], int)
        assert isinstance(row["face_type"], int)


def test_known_names_and_new_topup_rows():
    by_id = {row["arena_id"]: row for row in CARDS["cards"]}
    assert by_id["6873"]["chinese"] == "猛进犀群"
    assert by_id["21519"]["chinese"] == "穿越裂罅"
    assert by_id["46781"]["chinese"] == "裂镜奇奇几奇"
    assert by_id["107767"]["chinese"] == "仙儿君王瓯柯"
    # 17Lands top-up set row; absent from the 2026.64.50 registry run.
    assert by_id["106931"]["set_code"] == "SDS"
    assert by_id["106931"]["chinese"] == "月主教米凯耶"


def test_coverage_is_not_smaller_than_previous_snapshot():
    assert len(CARDS["cards"]) >= 25923
