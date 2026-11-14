"""Probe a frozen candidate using real macOS reopen events and synthetic data.

Usage: build-venv2/bin/python Tools/check_macos_reopen.py /path/to/candidate.app
The child has a disposable home, uses --offline-demo, and is addressed by PID.
No Accessibility permission, screen capture, game input or real profile is used.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


APPLE_EVENT = r"""
ObjC.import("Foundation");
function run(argv) {
    var kind = argv[1];
    var event = $.NSAppleEventDescriptor.appleEventWithEventClassEventIDTargetDescriptorReturnIDTransactionID(
        kind === "reopen" ? 0x61657674 : 0x6d697363,
        kind === "reopen" ? 0x72617070 : 0x646f7363,
        $.NSAppleEventDescriptor.descriptorWithProcessIdentifier(Number(argv[0])), -1, 0);
    if (kind !== "reopen") {
        event.setParamDescriptorForKeyword($.NSAppleEventDescriptor.descriptorWithString(argv[2]), 0x2d2d2d2d);
    }
    var error = Ref();
    var reply = event.sendEventWithOptionsTimeoutError(3, 3, error);
    if (reply.isNil()) throw Error(ObjC.unwrap(error[0].localizedDescription));
    var code = reply.paramDescriptorForKeyword(0x6572726e);
    if (!code.isNil() && code.int32Value !== 0) throw Error("Apple event failed: " + code.int32Value);
    return ObjC.unwrap(reply.paramDescriptorForKeyword(0x2d2d2d2d).stringValue) || "";
}
"""


def send(pid, script="", *, reopen=False):
    return subprocess.check_output(
        ["/usr/bin/osascript", "-l", "JavaScript", "-e", APPLE_EVENT,
         str(pid), "reopen" if reopen else "script", script],
        text=True, stderr=subprocess.PIPE, timeout=5,
    ).strip()


def wait_for(check, expected, process):
    deadline = time.monotonic() + 20
    last = ""
    while time.monotonic() < deadline:
        assert process.poll() is None, "Probe application exited"
        try:
            last = check()
            if last == expected:
                return
        except subprocess.CalledProcessError as error:
            last = error.stderr.strip()  # Tk may still be initializing.
        time.sleep(0.1)
    raise AssertionError(f"Expected {expected!r}, got {last!r}")


def main():
    app = Path(sys.argv[1]).resolve(strict=True)
    command = [str(app / "Contents/MacOS/MTGA_17Lands_ZH_Candidate")]
    with tempfile.TemporaryDirectory(prefix="mtga-dock-probe-") as directory:
        # Scope the existing candidate entry point to a subprocess-only home.
        env = dict(os.environ, HOME=directory)
        with (Path(directory) / "probe.log").open("w") as log:
            process = subprocess.Popen(
                [*command, "--offline-demo"], env=env, cwd=directory,
                stdout=log, stderr=log,
            )
            pid = process.pid
            try:
                wait_for(lambda: send(pid, "llength [info commands ::tk::mac::ReopenApplication]"),
                         "1", process)
                windows = send(pid, "winfo children .")
                scenarios = []
                for state in ("iconic", "withdrawn", "iconic", "normal"):
                    send(pid, f"wm state . {state}")
                    wait_for(lambda: send(pid, "wm state ."), state, process)
                    send(pid, reopen=True)
                    wait_for(lambda: send(pid, "list [wm state .] [winfo viewable .]"),
                             "normal 1", process)
                    assert send(pid, "winfo children .") == windows
                    scenarios.append({"before": state, "after": "normal", "viewable": True})

                # Invoke actual buttons, including all close/re-entry paths.
                send(pid, """
                    proc ::probe_find {w pattern} {
                        foreach c [winfo children $w] {
                            if {![catch {$c cget -command} command] &&
                                [string match $pattern $command]} {return $c}
                            set found [::probe_find $c $pattern]
                            if {$found ne ""} {return $found}
                        }
                        return ""
                    }
                """)
                close_paths = []
                for close_path in ("restore-button", "native-close", "destroyed-widget"):
                    send(pid, "[::probe_find . *_enable_overlay] invoke")
                    mini = send(pid, """
                        set restore [::probe_find . *_close_overlay]
                        if {$restore ne ""} {winfo toplevel $restore}
                    """)
                    assert mini.startswith("."), "Actual mini window was not created"
                    wait_for(lambda: send(pid, f"list [wm state .] [wm state {mini}] [winfo viewable {mini}]"),
                             "withdrawn normal 1", process)
                    send(pid, f"wm withdraw {mini}")
                    send(pid, reopen=True)
                    wait_for(lambda: send(pid, f"list [wm state .] [wm state {mini}] [winfo viewable {mini}]"),
                             "withdrawn normal 1", process)
                    if close_path == "restore-button":
                        close = f"[::probe_find {mini} *_close_overlay] invoke"
                    elif close_path == "native-close":
                        close = f"eval [wm protocol {mini} WM_DELETE_WINDOW]"
                    else:
                        close = f"destroy {mini}"
                    send(pid, f"if {{[winfo exists {mini}]}} {{{close}}}")
                    # Direct destruction intentionally bypasses the close handler;
                    # Dock must recover main and the next entry must replace the
                    # stale Python reference rather than returning early.
                    if close_path == "destroyed-widget":
                        send(pid, reopen=True)
                    wait_for(lambda: send(pid, "list [wm state .] [winfo viewable .]"),
                             "normal 1", process)
                    assert send(pid, f"winfo exists {mini}") == "0"
                    close_paths.append(close_path)
                # Prove the final, directly destroyed widget does not block entry.
                send(pid, "[::probe_find . *_enable_overlay] invoke")
                mini = send(pid, "winfo toplevel [::probe_find . *_close_overlay]")
                wait_for(lambda: send(pid, f"list [wm state .] [wm state {mini}] [winfo viewable {mini}]"),
                         "withdrawn normal 1", process)
                print(json.dumps({
                    "frozen_app": str(app), "pid": pid,
                    "native_reopen_scenarios": scenarios,
                    "mini_mode_restored_without_showing_main": True,
                    "return_from_mini_to_main": True,
                    "mini_close_paths": close_paths,
                    "native_close_restores_main_without_dock": True,
                    "mini_reentry_after_direct_destroy": True,
                    "same_process_and_windows": True,
                    "profile": "disposable synthetic offline demo",
                }, ensure_ascii=False, indent=2), flush=True)
            except Exception:
                log.flush()
                sys.stderr.write((Path(directory) / "probe.log").read_text())
                debug = (Path(directory) / "Library/Application Support/"
                         "MTGA_Draft_17Lands_ZH_Candidate/Debug/debug.log")
                if debug.exists():
                    sys.stderr.write(debug.read_text())
                try:
                    sys.stderr.write("Probe windows: " + send(pid, "list [wm state .] [winfo children .]") + "\n")
                except (subprocess.SubprocessError, AssertionError):
                    pass
                raise
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


if __name__ == "__main__":
    main()
