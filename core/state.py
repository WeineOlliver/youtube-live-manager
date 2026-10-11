import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
# Kept in client-secret/ (git-ignored) so the RTMP keys never get committed.
STREAM_KEY_PATH = os.path.join(BASE_DIR, "client-secret", "stream_key.txt")
STREAM_KEY_SHORTS_PATH = os.path.join(BASE_DIR, "client-secret", "stream_key_shorts.txt")

DEFAULT_PROFILE = {
    "name": "Nova Live",
    "title": "",
    "description": "",
    "tags": "",
    "thumbnail_normal": "",
    "thumbnail_shorts": "",
    "enable_fhd": True,
    "enable_shorts": True,
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


def _stream_key_path(kind: str) -> str:
    return STREAM_KEY_SHORTS_PATH if kind == "shorts" else STREAM_KEY_PATH


def load_stream_key(kind: str = "fhd") -> str:
    path = _stream_key_path(kind)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_stream_key(key: str, kind: str = "fhd") -> None:
    path = _stream_key_path(kind)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(key.strip())
