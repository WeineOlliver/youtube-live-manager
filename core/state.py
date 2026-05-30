import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

DEFAULT_PROFILE = {
    "name": "Nova Live",
    "title": "",
    "description": "",
    "tags": "",
    "thumbnail_normal": "",
    "thumbnail_shorts": "",
    "poll_fullhd_question": "",
    "poll_fullhd_options": "",
    "poll_shorts_question": "",
    "poll_shorts_options": "",
    "poll_fullhd_enabled": True,
    "poll_shorts_enabled": True,
}

DEFAULT_CONFIG = {
    "profiles": [DEFAULT_PROFILE.copy()],
    "active_profile_index": 0,
    "test_mode": False,
    "firefox_profile": "",
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Migration: if 'profiles' is missing, it's an old config
        if "profiles" not in data:
            old_profile = {k: v for k, v in data.items() if k in DEFAULT_PROFILE}
            old_profile["name"] = "Imported Profile"
            data = {
                "profiles": [old_profile],
                "active_profile_index": 0,
                "test_mode": data.get("test_mode", False),
                "firefox_profile": data.get("firefox_profile", ""),
            }
        
        return {**DEFAULT_CONFIG, **data}
    return DEFAULT_CONFIG.copy()


def save_config(data: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
