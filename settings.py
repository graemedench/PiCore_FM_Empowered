"""Sable settings -- the ONE source of truth for user preferences.

A single JSON file, written atomically (tmp + fsync + rename) to survive power
loss. The Volumio UI is a read-only mirror: getUIConfig renders from this file,
setUIConfig writes it back and pings the app to reload. There is no second store.
"""
import json
import os
import tempfile
import threading


# Graeme's FM4 radio/mix layout. It is intentionally separate from the general
# defaults so a normal install remains generic, while a personal preset (and
# the panel's Reset Shortcuts action) can restore this useful starting point.
GRAEME_SHORTCUTS = {
    "btn_5": {"action": "bbc_radio_2", "arg": "", "hold_action": "play_uri",
              "hold_arg": "http://www.radiofeeds.net/playlists/bauerflash.pls?station=clyde2-mp3 | Greatest Hits Radio (Glasgow & the West)"},
    "btn_6": {"action": "bbc_radio_4", "arg": "", "hold_action": "play_uri",
              "hold_arg": "http://www.radiofeeds.net/playlists/bauerflash.pls?station=absolute80s-mp3 | Absolute 80s"},
    "btn_7": {"action": "play_uri", "arg": "tidal://mymusic/mixes/account-1 | My Mix 1", "hold_action": "play_uri",
              "hold_arg": "tidal://mymusic/mixes/account-2 | TIDAL Mix"},
}

DEFAULTS = {
    "streaming_services": {"bbcsounds": True, "tidal": True,
                           "spoton": False, "qobuz": False},
    "library": {"refresh_minutes": 0},
    "display": {
        "screen": "modern",          # modern|spectrum
        "theme": "panel",            # panel|performance|cinema (when screen == modern)
        "spectrum_style": "bars",    # bars|dots|mirror|ribbon|vu (screen == spectrum)
        "brightness": "high",        # low|medium|high -> hardware.CONTRAST
        "transitions": True,         # crossfade between screens
        "rotate": 0,                 # panel rotation DEGREES (0 or 180). 180 =
                                     # mounted upside-down. Baked into the luma
                                     # device at init -> a change needs a restart.
    },
    "clock": {
        "show_seconds": False,
        "show_date": False,
    },
    "screensaver": {
        "clock_after_s": 300,        # paused/idle -> show the clock (0 = never)
        "dim_s": 120,                # idle -> dim (reduced contrast + pixel-shift)
        "idle_s": 3600,              # idle -> fade to OLED off (0 = never)
    },

    "audio": {
        "power_on_volume": None,
        "output": "fixed_line_out",       # fixed_line_out | lineout_variable | headphone_variable
        "menu_mode": "general",        # general (detected outputs) | personal (Graeme preset)
    },
    "playback": {
        # stop | track | playlist | random. Applied by the Playback menu and
        # remembered as the front-panel default.
        "mode": "stop",
    },
    "dac": {
        # Persisted HINT only. Tracks the remote INPUT button; user-correctable.
        "input_index": 0,
    },
    "ir": {"enabled": True, "profile": "Xiaomi IR for TV box",
           "pair_id": 0x15, "learned": {}},
    "power": {"shutdown_gpio": 26},
    "controls": {"leds_enabled": True},
    "buttons": {
        "btn_1": {"action": "play", "arg": "", "hold_action": "", "hold_arg": ""},
        "btn_2": {"action": "pause", "arg": "", "hold_action": "", "hold_arg": ""},
        "btn_3": {"action": "previous", "arg": "", "hold_action": "", "hold_arg": ""},
        "btn_4": {"action": "next", "arg": "", "hold_action": "", "hold_arg": ""},
        "btn_5": {"action": "random", "arg": "", "hold_action": "", "hold_arg": ""},
        "btn_6": {"action": "repeat", "arg": "", "hold_action": "", "hold_arg": ""},
        "btn_7": {"action": "none", "arg": "", "hold_action": "", "hold_arg": ""},
        # Button 8 is the power button (hold 2s -- see inputs/buttons.py). It
        # shipped as "none" here, which silently beat the "shutdown" default in
        # _BUTTON_ACTION: _get_button_action treats any truthy configured action
        # as an override, and the string "none" is truthy. Fresh installs got a
        # dead power button. Keep this in step with _BUTTON_ACTION.
        "btn_8": {"action": "save_track", "arg": "", "hold_action": "", "hold_arg": ""},
    },
    "_meta": {"rev": 4, "pcp_button_layout": 0},
}

_DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config", "settings.json",
)


def _deep_merge(base, overlay, path=()):
    """Overlay known keys onto a copy of base; ignore unknown keys."""
    out = dict(base)
    # Learned codes are a user-defined map rather than fixed schema keys.
    if path == ("ir", "learned"):
        return dict(overlay or {})
    for k, v in (overlay or {}).items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v, path + (k,))
        elif k in out:
            out[k] = v
    return out


class Settings:
    def __init__(self, path=None):
        self.path = path or _DEFAULT_PATH
        self._lock = threading.RLock()
        self._data = json.loads(json.dumps(DEFAULTS))
        self.load()

    def load(self):
        with self._lock:
            try:
                with open(self.path, "r") as fh:
                    raw = json.load(fh)
                self._data = _deep_merge(DEFAULTS, raw)
                if self._migrate():
                    self.save()
            except FileNotFoundError:
                self.save()
            except (ValueError, OSError):
                pass
            return self._data

    def _migrate(self):
        """Bring an on-disk file up to the current rev. Returns True if anything
        changed (caller persists it).

        A saved file always beats DEFAULTS, so fixing a bad default is not
        enough on its own -- every unit that has already written settings.json
        keeps the old value forever. Hence this.
        """
        changed = False
        rev = (self._data.get("_meta") or {}).get("rev", 1)
        if rev < 2:
            # rev 2: button 8 is the power button. It was written as "none",
            # which overrode the built-in "shutdown" and left the button dead.
            # Only rewrite the broken value -- a deliberate reassignment to
            # something other than "none" is the user's and stays untouched.
            btn8 = (self._data.get("buttons") or {}).get("btn_8")
            if isinstance(btn8, dict) and btn8.get("action") in (None, "", "none"):
                btn8["action"] = "shutdown"
                changed = True
        if rev < 2:
            self._data.setdefault("_meta", {})["rev"] = 2
            changed = True
        if rev < 3:
            self._data.setdefault("audio", {}).setdefault("menu_mode", "general")
            self._data.setdefault("_meta", {})["rev"] = 3
            changed = True
        if rev < 4:
            # rev 4: button long-press actions are first-class settings. The
            # deep merge deliberately discards unknown JSON keys, so defining
            # them above is what makes personal shortcut settings survive a
            # restart and future UI saves.
            self._data.setdefault("_meta", {})["rev"] = 4
            changed = True
        return changed

    def save(self):
        with self._lock:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), suffix=".tmp")
            try:
                with os.fdopen(fd, "w") as fh:
                    json.dump(self._data, fh, indent=2, sort_keys=True)
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(tmp, self.path)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)

    def get(self, *path, default=None):
        with self._lock:
            node = self._data
            for key in path:
                if not isinstance(node, dict) or key not in node:
                    return default
                node = node[key]
            return node

    def set(self, *path_and_value):
        *path, value = path_and_value
        with self._lock:
            node = self._data
            for key in path[:-1]:
                node = node.setdefault(key, {})
            node[path[-1]] = value
            self.save()

    def reset_shortcuts(self):
        """Restore buttons 5-7 without disturbing other panel preferences."""
        with self._lock:
            buttons = self._data.setdefault("buttons", {})
            # The Graeme installer selects the personal audio menu too. That is
            # the durable profile flag on older settings files as well.
            personal = self._data.get("audio", {}).get("menu_mode") == "personal"
            source = GRAEME_SHORTCUTS if personal else {
                key: dict(DEFAULTS["buttons"][key])
                for key in ("btn_5", "btn_6", "btn_7")
            }
            for key, value in source.items():
                buttons[key] = dict(value)
            self.save()

    def as_dict(self):
        with self._lock:
            return json.loads(json.dumps(self._data))
