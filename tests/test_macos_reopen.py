import tkinter
from unittest.mock import MagicMock

import pytest

from src.ui.macos_reopen import REOPEN_COMMAND, install_macos_reopen


def root_and_handler(get_window=None):
    root = MagicMock()
    root.tk.call.return_value = "aqua"
    install_macos_reopen(root, get_window or (lambda: root))
    root.createcommand.assert_called_once()
    name, handler = root.createcommand.call_args.args
    assert name == REOPEN_COMMAND
    return root, handler


def test_registering_does_not_show_startup_window():
    root, _ = root_and_handler()
    root.deiconify.assert_not_called()
    root.lift.assert_not_called()
    root.focus_force.assert_not_called()


def test_dock_reopen_restores_existing_window_repeatedly():
    root, reopen = root_and_handler()
    for _ in range(3):
        reopen()
    assert root.deiconify.call_count == 3
    assert root.lift.call_count == 3
    assert root.focus_force.call_count == 3


def test_mini_mode_is_resolved_at_click_time():
    current = [None]
    root, reopen = root_and_handler(lambda: current[0])
    overlay = MagicMock()
    current[0] = overlay
    reopen()
    overlay.deiconify.assert_called_once()
    overlay.lift.assert_called_once()
    overlay.focus_force.assert_called_once()
    root.deiconify.assert_not_called()
    current[0] = None
    reopen()
    root.deiconify.assert_called_once()


def test_destroyed_overlay_falls_back_to_main_window():
    overlay = MagicMock()
    overlay.winfo_exists.return_value = False
    root, reopen = root_and_handler(lambda: overlay)
    reopen()
    root.deiconify.assert_called_once()
    overlay.deiconify.assert_not_called()


def test_queued_reopen_during_shutdown_is_harmless():
    root, reopen = root_and_handler()
    root.winfo_exists.return_value = False
    reopen()
    root.deiconify.assert_not_called()


def test_window_disappearing_during_restore_is_harmless():
    root, reopen = root_and_handler()
    root.deiconify.side_effect = tkinter.TclError("window destroyed")
    reopen()
    root.focus_force.assert_not_called()


@pytest.mark.parametrize("window_system", ["win32", "x11"])
def test_other_platforms_are_unchanged(window_system):
    root = MagicMock()
    root.tk.call.return_value = window_system
    install_macos_reopen(root, lambda: root)
    root.createcommand.assert_not_called()
