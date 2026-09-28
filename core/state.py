import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
# Kept in client-secret/ (git-ignored) so the RTMP key never gets committed.
STREAM_KEY_PATH = os.path.join(BASE_DIR, "client-secret", "stream_key.txt")

DEFAULT_PROFILE = {
    "name": "Nova Live",
    "title": "",
    "description": "",
    "tags": "",
    "thumbnail_normal": "",
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


def load_stream_key() -> str:
    if not os.path.exists(STREAM_KEY_PATH):
        return ""
    with open(STREAM_KEY_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_stream_key(key: str) -> None:
    os.makedirs(os.path.dirname(STREAM_KEY_PATH), exist_ok=True)
    with open(STREAM_KEY_PATH, "w", encoding="utf-8") as f:
        f.write(key.strip())
