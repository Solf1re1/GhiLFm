"""
Profile & Preset Manager.
Handles saving and loading full application state, presets, and sequences to/from JSON.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional

def _get_profiles_dir() -> str:
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
        app_profiles = os.path.join(base_dir, "profiles")
        try:
            os.makedirs(app_profiles, exist_ok=True)
            return app_profiles
        except Exception:
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            user_dir = os.path.join(appdata, "ApexClicker", "profiles")
            os.makedirs(user_dir, exist_ok=True)
            return user_dir
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiles")

PROFILES_DIR = _get_profiles_dir()


DEFAULT_PRESETS = {
    "Minecraft_PVP_Humanized": {
        "mode": "BURST",
        "burst_config": {
            "target_mode": "CURRENT",
            "fixed_x": 0,
            "fixed_y": 0,
            "button": "left",
            "interval": 0.05,  # 20 CPS
            "repeat_limit": 0,
            "humanizer_enabled": True,
            "jitter_percent": 0.18,
            "jitter_radius": 2,
            "fatigue_enabled": True,
        },
    },
    "Insane_Burst_500CPS": {
        "mode": "BURST",
        "burst_config": {
            "target_mode": "CURRENT",
            "fixed_x": 0,
            "fixed_y": 0,
            "button": "left",
            "interval": 0.002,  # 500 CPS
            "repeat_limit": 0,
            "humanizer_enabled": False,
            "jitter_percent": 0.0,
            "jitter_radius": 0,
            "fatigue_enabled": False,
        },
    },
    "AFK_Anti_Idle_Safe": {
        "mode": "BURST",
        "burst_config": {
            "target_mode": "CURRENT",
            "fixed_x": 0,
            "fixed_y": 0,
            "button": "left",
            "interval": 15.0,  # 1 click every 15s
            "repeat_limit": 0,
            "humanizer_enabled": True,
            "jitter_percent": 0.30,
            "jitter_radius": 4,
            "fatigue_enabled": False,
        },
    },
    "Demo_Multi_Point_Sequence": {
        "mode": "SEQUENCE",
        "sequence_config": {
            "repeat_count": 5,
            "humanizer_enabled": True,
            "points": [
                {"x": 400, "y": 300, "button": "left", "delay": 0.5, "jitter_radius": 3, "smooth_move": True, "move_duration": 0.3},
                {"x": 600, "y": 300, "button": "left", "delay": 0.5, "jitter_radius": 3, "smooth_move": True, "move_duration": 0.3},
                {"x": 500, "y": 500, "button": "right", "delay": 0.8, "jitter_radius": 3, "smooth_move": True, "move_duration": 0.3},
            ],
        },
    },
}


class ProfileManager:
    """Saves and restores configuration profiles."""

    @classmethod
    def ensure_dir(cls):
        os.makedirs(PROFILES_DIR, exist_ok=True)
        # Create built-in preset files if empty
        for name, preset_data in DEFAULT_PRESETS.items():
            path = os.path.join(PROFILES_DIR, f"{name}.json")
            if not os.path.exists(path):
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(preset_data, f, indent=2)
                except Exception:
                    pass

    @classmethod
    def list_profiles(cls) -> List[str]:
        """Returns all available profile names."""
        cls.ensure_dir()
        try:
            files = [
                f[:-5]
                for f in os.listdir(PROFILES_DIR)
                if f.endswith(".json") and os.path.isfile(os.path.join(PROFILES_DIR, f))
            ]
            return sorted(files)
        except Exception:
            return []

    @classmethod
    def save_profile(cls, name: str, data: Dict[str, Any]) -> bool:
        """Saves configuration data into a named profile."""
        cls.ensure_dir()
        clean_name = "".join(c for c in name if c.isalnum() or c in ("_", "-")).strip()
        if not clean_name:
            return False
        path = os.path.join(PROFILES_DIR, f"{clean_name}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False

    @classmethod
    def load_profile(cls, name: str) -> Optional[Dict[str, Any]]:
        """Loads configuration data from a named profile."""
        cls.ensure_dir()
        path = os.path.join(PROFILES_DIR, f"{name}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
