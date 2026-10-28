import gc
import threading
from unittest.mock import MagicMock

import pytest

from src.ui.tk_gc import TkGCGuard


def test_collection_is_scheduled_and_previous_gc_setting_restored():
    before = gc.isenabled()
    root = MagicMock()
    root.after.return_value = "gc-timer"
    with TkGCGuard() as guard:
        assert not gc.isenabled()
        guard.attach(root)
        root.after.call_args.args[1]()
        assert guard.collections == 1
    root.after_cancel.assert_called_once_with("gc-timer")
    assert gc.isenabled() == before


def test_already_disabled_gc_stays_disabled():
    before = gc.isenabled()
    gc.disable()
    try:
        with TkGCGuard():
            pass
        assert not gc.isenabled()
    finally:
        if before:
            gc.enable()


def test_worker_cannot_enter_or_attach_or_collect():
    root = MagicMock()
    errors = []
    with TkGCGuard() as guard:
        guard.attach(root)
        collect = root.after.call_args.args[1]

        def work():
            for action in [lambda: TkGCGuard().__enter__(),
                           lambda: guard.attach(root), collect]:
                try:
                    action()
                except RuntimeError as error:
                    errors.append(str(error))

        thread = threading.Thread(target=work)
        thread.start()
        thread.join(3)
        assert not thread.is_alive()
        assert len(errors) == 3
        assert guard.collections == 0


def test_attach_requires_context():
    with pytest.raises(RuntimeError, match="Enter TkGCGuard"):
        TkGCGuard().attach(MagicMock())
