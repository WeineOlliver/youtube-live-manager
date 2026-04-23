import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

DEFAULT_CONFIG = {
    "title": "",
    "description": "",
    "tags": "",
    "thumbnail_normal": "",
    "thumbnail_shorts": "",
    "poll_fullhd_question": "",
    "poll_fullhd_options": "",
    "poll_shorts_question": "",
    "poll_shorts_options": "",
    "test_mode": False,
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULT_CONFIG, **data}
    return DEFAULT_CONFIG.copy()


def save_config(data: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
