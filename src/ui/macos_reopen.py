"""Restore the active application window when macOS sends a Dock reopen event."""
import logging
import tkinter

logger = logging.getLogger(__name__)
REOPEN_COMMAND = "::tk::mac::ReopenApplication"


def install_macos_reopen(root, get_window):
    """Keep macOS activation separate from startup and mini-mode visibility.

    Tk does not supply ReopenApplication in the bundled Aqua runtime. Register
    it only after the UI is ready, and resolve the window at click time so a
    hidden main window stays hidden while the user is in mini mode.
    """
    if root.tk.call("tk", "windowingsystem") != "aqua":
        return

    def reopen():
        try:
            if not root.winfo_exists():
                return
            window = get_window()
            if window is None or not window.winfo_exists():
                window = root
            window.deiconify()
            window.lift()
            window.focus_force()
        except tkinter.TclError:
            # A queued Dock event may arrive while the application is closing.
            logger.debug("Window closed before the Dock reopen event completed")

    root.createcommand(REOPEN_COMMAND, reopen)
