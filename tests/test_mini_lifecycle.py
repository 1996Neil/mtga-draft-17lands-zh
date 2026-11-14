import tkinter
from unittest.mock import MagicMock, patch

import pytest

from src.ui.app import DraftApp
from src.ui.windows.overlay import CompactOverlay


def make_app(overlay=None):
    app = DraftApp.__new__(DraftApp)
    app.root = MagicMock()
    app.configuration = MagicMock()
    app.overlay_window = overlay
    app._refresh_ui_data = MagicMock()
    return app


@pytest.mark.parametrize("missing", [False, tkinter.TclError("destroyed")])
def test_entering_mini_replaces_destroyed_reference(missing):
    old = MagicMock()
    if isinstance(missing, Exception):
        old.winfo_exists.side_effect = missing
    else:
        old.winfo_exists.return_value = missing
    app = make_app(old)
    with patch("src.ui.app.CompactOverlay") as constructor:
        app._enable_overlay()
        assert app.overlay_window is constructor.return_value
        constructor.assert_called_once_with(
            app.root, app, app.configuration, app._disable_overlay
        )
        constructor.return_value.deiconify.assert_called_once()
        app.root.withdraw.assert_called_once()


def test_existing_mini_is_shown_without_creating_another():
    overlay = MagicMock()
    app = make_app(overlay)
    with patch("src.ui.app.CompactOverlay") as constructor:
        app._enable_overlay()
        constructor.assert_not_called()
    overlay.deiconify.assert_called_once()
    overlay.lift.assert_called_once()
    overlay.focus_force.assert_called_once()
    app.root.withdraw.assert_called_once()


def test_constructor_failure_keeps_main_window_visible():
    app = make_app()
    with patch("src.ui.app.CompactOverlay", side_effect=RuntimeError("failed")):
        with pytest.raises(RuntimeError, match="failed"):
            app._enable_overlay()
    app.root.withdraw.assert_not_called()
    assert app.overlay_window is None


def test_returning_from_destroyed_mini_clears_reference():
    overlay = MagicMock()
    overlay.winfo_exists.return_value = False
    app = make_app(overlay)
    with patch("src.ui.app.Theme.apply"):
        app._disable_overlay()
    assert app.overlay_window is None
    overlay.destroy.assert_not_called()
    app.root.deiconify.assert_called_once()


def test_close_restores_main_even_if_geometry_cannot_be_saved():
    overlay = MagicMock()
    overlay._save_geometry.side_effect = OSError("read-only")
    with pytest.raises(OSError, match="read-only"):
        CompactOverlay._close_overlay(overlay)
    overlay.on_restore.assert_called_once()
