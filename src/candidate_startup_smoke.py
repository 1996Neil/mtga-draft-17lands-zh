"""Explicit native integration check of the normal splash/reader startup path."""
import gc
import hashlib
import json
import threading
import tkinter
from pathlib import Path


def run(gc_guard):
    import main
    from src import constants
    from src.card_display import DISPLAY

    original_app = main.DraftApp
    collected_threads = []

    def observe_gc(phase, _):
        if phase == "start":
            collected_threads.append(threading.current_thread().name)

    gc.callbacks.append(observe_gc)

    class StartupProbe(original_app):
        def __init__(self, root, scanner, config):
            super().__init__(root, scanner, config)
            self._smoke_ticks = 0
            self._initial_hash = self._raw_hash()
            root.after(100, self._tick)
            root.after(10000, self._finish)

        def _raw_hash(self):
            raw = self.orchestrator.scanner.set_data.get_card_ratings()
            return hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()

        def _tick(self):
            self._smoke_ticks += 1
            # Discard a genuine Tcl variable cycle on the UI thread. Allocation
            # in asynchronous readers must not finalize it on their thread.
            variable = tkinter.StringVar(master=self.root, value="startup-gc-probe")
            variable.cycle = variable
            self.root.after(100, self._tick)

        def _finish(self):
            assert self._initialized and self.orchestrator.is_alive()
            assert self._smoke_ticks >= 30
            assert not DISPLAY.pending
            assert gc_guard.collections > 0
            assert collected_threads and set(collected_threads) == {"MainThread"}
            self._apply_language(False)
            self._apply_language(True)
            assert self._initial_hash == self._raw_hash()
            result = {"normal_splash_to_ui": True,
                      "orchestrator_running": True,
                      "pack_rows": len(self.current_pack_data),
                      "cards_with_gihwr": sum(c.get("deck_colors", {}).get("All Decks", {}).get("gihwr", 0) > 0 for c in self.current_pack_data),
                      "download_default_set": self.panel_data.vars["set"].get(),
                      "download_default_event": self.panel_data.vars["event"].get(),
                      "heartbeat_ticks": self._smoke_ticks,
                      "main_thread_gc_collections": gc_guard.collections,
                      "collection_threads": sorted(set(collected_threads)),
                      "raw_data_unchanged": True,
                      "native_tk": self.root.tk.call("info", "patchlevel")}
            settings = self.configuration.settings
            if (settings.chinese_enabled and settings.auto_update_chinese_names and
                    not settings.chinese_source_path):
                from src.names_update import store_version
                assert self.controller._names_started
                store = Path(constants.BASE_DIR) / "Names/chinese-names.sqlite"
                assert store.is_file()
                result["automatic_names_version"], result["automatic_names_rows"] = store_version(store)
                result["names_worker_finished"] = not any(
                    thread.name == "chinese-names-update" for thread in threading.enumerate()
                )
                # A valid multi-version delta can still be downloading here.
                # Controlled idle-startup probes assert this separately.
            path = Path(constants.BASE_DIR) / "startup-smoke-result.json"
            path.write_text(json.dumps(result, indent=2))
            print(json.dumps(result), flush=True)
            self._on_close()

    main.DraftApp = StartupProbe
    try:
        main.main(gc_guard=gc_guard)
    finally:
        main.DraftApp = original_app
        gc.callbacks.remove(observe_gc)
