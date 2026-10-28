"""Route Tk calls made from worker threads onto the UI thread.

Tkinter is not thread safe: calling ``after`` (or anything else that reaches
Tcl) from a worker can corrupt the interpreter's heap. The visible symptom was
a SIGSEGV inside canvas drawing seconds after startup, with a worker stack in
``suggest_deck._worker`` at the same moment.

``install(root)`` patches ``Misc.after`` so that worker-thread callbacks are
queued and scheduled from the UI thread instead of touching Tcl directly.
Main-thread calls keep their original behaviour and return real timer ids.
"""
import queue
import threading
import tkinter

_PENDING = queue.Queue()
_ORIGINAL_AFTER = None
_INSTALLED = False
PUMP_MS = 20


def _pump(root):
    while True:
        try:
            widget, delay, func, args, kwargs = _PENDING.get_nowait()
        except queue.Empty:
            break
        if func is None:
            continue
        try:
            if widget.winfo_exists():
                _ORIGINAL_AFTER(widget, delay, func, *args, **kwargs)
        except Exception:
            # The widget may have gone away between queueing and pumping.
            pass
    try:
        _ORIGINAL_AFTER(root, PUMP_MS, _pump, root)
    except Exception:
        pass


def install(root):
    """Patch Misc.after once and start the pump on the UI thread."""
    global _ORIGINAL_AFTER, _INSTALLED
    if _INSTALLED or root is None:
        return
    _ORIGINAL_AFTER = tkinter.Misc.after
    main_thread = threading.main_thread()

    def after(self, ms, func=None, *args, **kwargs):
        if threading.current_thread() is main_thread:
            return _ORIGINAL_AFTER(self, ms, func, *args, **kwargs)
        # Worker thread: never touch Tcl here.
        _PENDING.put((self, ms, func, args, kwargs))
        return "queued-on-ui-thread"

    tkinter.Misc.after = after
    _INSTALLED = True
    _ORIGINAL_AFTER(root, PUMP_MS, _pump, root)
