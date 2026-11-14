import copy
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
from unittest.mock import patch

import pytest

from src import names_update as names
from src.card_display import read_source


def row(aid="1", chinese="卡牌"):
    return {"arena_id": aid, "english": "Card" + aid, "chinese": chinese,
            "set_code": "TST", "primary": 1, "face_type": 0, "source": "fixture",
            "status": "static-verified-client-pending"}


@pytest.fixture
def base(tmp_path):
    bundled = tmp_path / "cards.json"
    pin = {"data_version": "2026.65.0-r1", "cards_jsonl_sha256": "a" * 64, "rows": 2}
    bundled.write_text(json.dumps({"schema": 1, "data_version": pin["data_version"], "source_sha256": "a" * 64,
                                   "cards": [row(), row("2", "保留")]}))
    store = tmp_path / "names.sqlite"
    names.seed_store(store, bundled, pin)
    return store, bundled, pin


def delta(old="2026.65.0-r1", new="2026.65.0-r2", *, upserts=None, removes=None, count=2):
    data = {"schema": 1, "from": old, "to": new, "rows": count,
            "upserts": [row(chinese="修正")] if upserts is None else upserts,
            "removes": [] if removes is None else removes}
    raw = gzip.compress(json.dumps(data, ensure_ascii=False).encode(), mtime=0)
    sha = hashlib.sha256(raw).hexdigest()
    edge = {"from": old, "to": new, "rows": count, "upserts": len(data["upserts"]),
            "removes": len(data["removes"]), "file": f"patches/{sha}.json.gz",
            "sha256": sha, "bytes": len(raw)}
    return edge, raw


def downloader(edges=(), payloads=(), version=None):
    index = {"schema": 1, "version": version or (edges[-1]["to"] if edges else "2026.65.0-r1"),
             "rows": edges[-1]["rows"] if edges else 2, "patches": list(edges)}
    bodies = {"latest.json": json.dumps(index).encode(), **dict(zip([e["file"] for e in edges], payloads))}
    calls = []

    def fetch(relative, limit):
        calls.append(relative)
        return bodies[relative]

    return fetch, calls


def test_idle_only_reads_metadata_and_one_small_request(base):
    store, bundled, pin = base
    fetch, calls = downloader()
    # Prove startup does not reopen/revalidate bundled or installed full rows.
    bundled.unlink()
    with patch.object(names, "validate_row", side_effect=AssertionError("full rescan")):
        result = names.check_once(store, bundled, pin, fetch)
    assert result == {"status": "current", "version": "2026.65.0-r1", "rows": 2, "changed": 0}
    assert calls == ["latest.json"]


def test_one_change_updates_only_changed_record(base):
    store, bundled, pin = base
    edge, raw = delta()
    fetch, calls = downloader([edge], [raw])
    with patch.object(names, "validate_row", wraps=names.validate_row) as validate:
        result = names.check_once(store, bundled, pin, fetch)
    assert result["changed"] == 1
    assert validate.call_count == 1
    assert calls == ["latest.json", edge["file"]]
    records = {r.arena_id: r for r in read_source(store)}
    assert records["1"].chinese == "修正" and records["2"].chinese == "保留"
    assert names.store_version(store)[0] == "2026.65.0-r2"


def test_add_remove_and_version_retry(base):
    store, bundled, pin = base
    edge, raw = delta(upserts=[row("3", "新增")], removes=["1"])
    fetch, calls = downloader([edge], [raw])
    names.check_once(store, bundled, pin, fetch)
    assert {r.arena_id for r in read_source(store)} == {"2", "3"}
    calls.clear()
    with patch.object(names, "validate_row", side_effect=AssertionError("revalidation")):
        names.check_once(store, bundled, pin, fetch)
    assert calls == ["latest.json"]


def test_chain_failure_rolls_back_all_rows_and_version(base):
    store, bundled, pin = base
    first, raw1 = delta()
    second, raw2 = delta("2026.65.0-r2", "2026.65.0-r3")
    fetch, _ = downloader([first, second], [raw1, raw2 + b"corrupt"])
    with pytest.raises(ValueError, match="hash"):
        names.check_once(store, bundled, pin, fetch)
    assert names.store_version(store)[0] == "2026.65.0-r1"
    assert next(r for r in read_source(store) if r.arena_id == "1").chinese == "卡牌"


@pytest.mark.parametrize("fault", ["markup", "fields", "missing-removal", "count", "duplicate"])
def test_bad_patch_keeps_old_version(base, fault):
    store, bundled, pin = base
    changed = row()
    if fault == "markup":
        changed["chinese"] = "<b>卡</b>"
    if fault == "fields":
        changed["oracle_text"] = "not a name"
    edge, raw = delta(upserts=[changed, changed] if fault == "duplicate" else [changed],
                      removes=["99"] if fault == "missing-removal" else [],
                      count=99 if fault == "count" else 2)
    fetch, _ = downloader([edge], [raw])
    with pytest.raises(ValueError):
        names.check_once(store, bundled, pin, fetch)
    assert names.store_version(store)[0] == "2026.65.0-r1"


def test_offline_keeps_seed_and_does_not_retry(base):
    store, bundled, pin = base
    calls = []
    def offline(relative, limit):
        calls.append(relative)
        raise OSError("offline")
    with pytest.raises(OSError):
        names.check_once(store, bundled, pin, offline)
    assert calls == ["latest.json"]
    assert len(read_source(store)) == 2


def test_skip_versions_via_two_small_patches(base):
    store, bundled, pin = base
    e1, r1 = delta()
    e2, r2 = delta("2026.65.0-r2", "2026.65.0-r3", upserts=[row("2", "又修正")])
    fetch, calls = downloader([e1, e2], [r1, r2])
    result = names.check_once(store, bundled, pin, fetch)
    assert result["version"] == "2026.65.0-r3" and result["changed"] == 2
    assert len(calls) == 3


def test_no_path_does_not_fall_back_to_full_package(base):
    store, bundled, pin = base
    fetch, calls = downloader(version="2026.65.0-r9")
    with pytest.raises(ValueError, match="No incremental path"):
        names.check_once(store, bundled, pin, fetch)
    assert calls == ["latest.json"]


def test_newer_local_version_is_never_downgraded(base):
    store, bundled, pin = base
    fetch, calls = downloader(version="2026.64.50-r5")
    assert names.check_once(store, bundled, pin, fetch)["status"] == "current"
    assert calls == ["latest.json"]


def test_paths_and_work_budget_are_bounded():
    edge, _ = delta()
    index = {"schema": 1, "version": edge["to"], "rows": 2, "patches": [edge]}
    for value in ("../credentials", "https://other.example/x"):
        malformed = copy.deepcopy(index)
        malformed["patches"][0]["file"] = value
        with pytest.raises(ValueError):
            names.plan_updates(malformed, edge["from"])
    malformed = copy.deepcopy(index)
    malformed["patches"][0]["bytes"] = 9 * 1024 * 1024
    with pytest.raises(ValueError):
        names.plan_updates(malformed, edge["from"])


def test_concurrent_startups_only_have_one_flight(base):
    store, bundled, pin = base
    assert names._FLIGHT.acquire(blocking=False)
    try:
        def forbidden(*args):
            raise AssertionError("second request")
        assert names.check_once(store, bundled, pin, forbidden) == {"status": "busy"}
    finally:
        names._FLIGHT.release()


def test_partial_transaction_does_not_leak_to_display_readers(base):
    store, bundled, pin = base
    with sqlite3.connect(store) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE names SET payload=? WHERE id='1'", (json.dumps(row(chinese="未提交")),))
        assert next(r for r in read_source(store) if r.arena_id == "1").chinese == "卡牌"
        db.rollback()


def test_controller_does_not_reload_an_unchanged_store(base, monkeypatch):
    from unittest.mock import MagicMock
    from src.ui.app_controller import AppController
    app = MagicMock()
    controller = AppController(app)
    store, _, _ = base
    controller._names_source = str(store)
    controller._names_version = "2026.65.0-r1"
    controller._names_results.put((str(store), "2026.65.0-r1"))
    app.orchestrator.update_queue.get_nowait.side_effect = __import__("queue").Empty()
    with patch.object(controller, "sync_display") as sync:
        controller.update_loop()
    assert not any(call.kwargs.get("force") for call in sync.call_args_list)


def test_controller_disabled_network_keeps_local_names(base, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import MagicMock
    from src.ui.app_controller import AppController
    from src import constants
    store, _, _ = base
    profile = store.parent
    target = profile / "Names/chinese-names.sqlite"
    target.parent.mkdir()
    store.rename(target)
    monkeypatch.setattr(constants, "BASE_DIR", str(profile))
    app = MagicMock()
    app.configuration.settings = SimpleNamespace(
        chinese_enabled=True, auto_update_chinese_names=False, chinese_source_path=""
    )
    controller = AppController(app)
    with patch("src.ui.app_controller.DISPLAY.request") as display:
        controller.sync_display()
    assert display.call_args.args[1] == str(target)
    with patch("src.ui.app_controller.threading.Thread") as worker:
        controller.start_names_update()
        controller.start_names_update()
    worker.assert_not_called()
