#!/usr/bin/env python3
"""
JellyRPC Daemon — window/idle presence for Discord
KDE Wayland compatible — detects running apps via pgrep, priority order wins.
"""

import json, subprocess, sys, time
from pathlib import Path

try:
    from pypresence import Presence, PyPresenceException
except ImportError:
    print("[jellyrpc] install pypresence: pip install pypresence --break-system-packages", file=sys.stderr)
    sys.exit(1)

POLL_SECS   = 5
IDLE_THRESH = 300
DEBOUNCE    = 2

CONFIG_DIR  = Path.home() / ".config" / "jellyrpc"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_CONFIG = {
    "discord_app_id":   "",
    "idle_detection":   True,
    "window_detection": True,
}

# Priority order — first running app wins.
# Put things you'd rather show above things you wouldn't.
APP_MAP = [
    ("nvim",      "Coding",           "Neovim",    "coding"),
    ("code",      "Coding",           "VSCode",    "coding"),
    ("zed",       "Coding",           "Zed",       "coding"),
    ("konsole",   "In a terminal",    "Konsole",   "terminal"),
    ("kitty",     "In a terminal",    "kitty",     "terminal"),
    ("alacritty", "In a terminal",    "Alacritty", "terminal"),
    ("foot",      "In a terminal",    "foot",      "terminal"),
    ("steam",     "On Steam",         "Steam",     "steam"),
    ("obsidian",  "Writing notes",    "Obsidian",  "coding"),
    ("gimp",      "Editing images",   "GIMP",      "coding"),
    ("blender",   "3D modelling",     "Blender",   "coding"),
    ("firefox",   "Browsing the web", "Firefox",   "firefox"),
    ("chromium",  "Browsing the web", "Chromium",  "firefox"),
    ("chrome",    "Browsing the web", "Chrome",    "firefox"),
]

def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
    try:
        with open(CONFIG_FILE) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception:
        return DEFAULT_CONFIG

def run(cmd, timeout=2):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""

def detect_app():
    for name, details, state, icon in APP_MAP:
        if run(["pgrep", "-x", name]):
            return details, state, icon
    return None, None, None

def get_idle_ms():
    for cmd in [["xssstate", "-i"], ["xprintidle"]]:
        out = run(cmd)
        if out.isdigit():
            return int(out)
    return None

def mprisence_active():
    if run(["systemctl", "--user", "is-active", "mprisence"]) != "active":
        return False
    return run(["playerctl", "status"]) in ("Playing", "Paused")

def main():
    cfg = load_config()
    app_id = cfg.get("discord_app_id", "")
    if not app_id:
        print("[jellyrpc] discord_app_id not set in ~/.config/jellyrpc/config.json — exiting", file=sys.stderr)
        sys.exit(1)

    rpc = None
    connected = False
    last_state = None
    retry = 0
    candidates = []

    print(f"[jellyrpc] starting (app id: {app_id})", file=sys.stderr)

    while True:
        try:
            if not connected:
                try:
                    rpc = Presence(app_id)
                    rpc.connect()
                    connected = True
                    retry = 0
                    print("[jellyrpc] connected to Discord", file=sys.stderr)
                except Exception as e:
                    retry += 1
                    wait = min(30, retry * 5)
                    print(f"[jellyrpc] Discord not reachable, retry in {wait}s", file=sys.stderr)
                    time.sleep(wait)
                    continue

            # ── candidate this tick ───────────────────────────────────────
            if mprisence_active():
                candidate = ("mprisence", None, None, None)
            elif cfg["idle_detection"] and (idle_ms := get_idle_ms()) is not None and idle_ms / 1000 >= IDLE_THRESH:
                candidate = ("idle", "Away from keyboard", "", "idle")
            elif cfg["window_detection"]:
                details, state, icon = detect_app()
                candidate = ("app", details, state, icon) if details else ("cleared", None, None, None)
            else:
                candidate = ("cleared", None, None, None)

            # ── debounce ──────────────────────────────────────────────────
            candidates.append(candidate)
            if len(candidates) > DEBOUNCE:
                candidates.pop(0)
            if len(candidates) < DEBOUNCE or len(set(candidates)) > 1:
                time.sleep(POLL_SECS)
                continue

            agreed = candidates[0]
            if agreed == last_state:
                time.sleep(POLL_SECS)
                continue

            # ── apply ─────────────────────────────────────────────────────
            kind, details, state, icon = agreed
            if kind == "mprisence":
                rpc.clear()
                print("[jellyrpc] mprisence active — silent", file=sys.stderr)
            elif kind == "idle":
                rpc.update(details="Away from keyboard", large_image="idle", large_text="Idle")
                print("[jellyrpc] idle", file=sys.stderr)
            elif kind == "app":
                rpc.update(details=details, state=state, large_image=icon, large_text=details)
                print(f"[jellyrpc] {details} — {state}", file=sys.stderr)
            else:
                rpc.clear()
                print("[jellyrpc] cleared", file=sys.stderr)

            last_state = agreed

        except (PyPresenceException, Exception) as e:
            print(f"[jellyrpc] error: {e}", file=sys.stderr)
            connected = False
            rpc = None
            candidates = []
            last_state = None
            time.sleep(5)
            continue

        time.sleep(POLL_SECS)

if __name__ == "__main__":
    main()
