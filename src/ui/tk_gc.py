"""Keep cyclic Tk finalizers on the UI thread in the isolated Mac candidate.

Python may otherwise collect discarded widgets/variables on an allocating
worker (for example the Chinese index reader). Their finalizers call Tcl.
Reference counting remains enabled; only cyclic collection is scheduled here.
"""
import gc
import threading
import time
import weakref
import tkinter


class TkGCGuard:
    """Collect cyclic garbage from the UI thread, cheaply.

    A full ``gc.collect()`` every second walked the whole heap (the dataset and
    card objects dominate it) and showed up as ~20% idle CPU, which is what made
    window dragging stutter. Young generations are collected often and cheaply;
    the expensive full pass runs rarely.
    """

    def __init__(self, interval_ms=1000, full_interval_s=120):
        self.interval_ms = interval_ms
        self.full_interval_s = full_interval_s
        self._last_full = time.monotonic()
        self._roots = []
        self._enabled_before = False
        self.active = False
        self.collections = 0

    @staticmethod
    def _require_main_thread():
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("Tk garbage collection must run on the main thread")

    def __enter__(self):
        self._require_main_thread()
        self._enabled_before = gc.isenabled()
        gc.disable()
        self.active = True
        return self

    def attach(self, root):
        self._require_main_thread()
        if not self.active:
            raise RuntimeError("Enter TkGCGuard before attaching a window")
        entry = [weakref.ref(root), None]
        self._roots.append(entry)

        def collect():
            self._require_main_thread()
            window = entry[0]()
            if not self.active or window is None:
                return
            now = time.monotonic()
            if now - self._last_full >= self.full_interval_s:
                gc.collect()
                self._last_full = now
            else:
                gc.collect(0)
            self.collections += 1
            entry[1] = window.after(self.interval_ms, collect)

        entry[1] = root.after(self.interval_ms, collect)

    def __exit__(self, *_):
        self._require_main_thread()
        self.active = False
        for reference, job in self._roots:
            root = reference()
            if root is not None and job is not None:
                try:
                    root.after_cancel(job)
                except tkinter.TclError:
                    pass  # The window may already have been destroyed.
        self._roots.clear()
        gc.collect()
        if self._enabled_before:
            gc.enable()
