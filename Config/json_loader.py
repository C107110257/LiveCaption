from pathlib import Path
import json
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    base_dir = get_base_dir()
    config_file = base_dir / "config.json"
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)