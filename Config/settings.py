from pathlib import Path

from .json_loader import load_config, get_base_dir
from .model_provisioning.model_resolver import resolve_model_path
from .system_info import get_thread_counts


config = load_config()

BASE_DIR = get_base_dir()
REMOTE_MODELS_DIR = config["models_dir"]
LOCAL_MODELS_DIR = BASE_DIR / "models"
MODEL_REQUIRED_FILES = config.get("model_required_files", {})
HUGGINGFACE_REPOS = config.get("huggingface_repos", {})
PREFER_HUGGINGFACE = config.get("prefer_huggingface", True)


def _resolve(model_key: str) -> str:
    return resolve_model_path(
        model_name=config[model_key],
        remote_models_dir=REMOTE_MODELS_DIR,
        local_models_dir=LOCAL_MODELS_DIR,
        required_files_map=MODEL_REQUIRED_FILES,
        huggingface_repos=HUGGINGFACE_REPOS,
        prefer_huggingface=PREFER_HUGGINGFACE,
    )


whisper_model = _resolve("whisper_model")
translate_model = _resolve("translate_model")
translate_model_ct2 = _resolve("translate_model_ct2")

for model_path in (whisper_model, translate_model, translate_model_ct2):
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model does not exist: {model_path}")

print("[Startup] All models ready.")

WHISPER_CPU_THREADS, TRANSLATOR_INTRA_THREADS = get_thread_counts(config)

DEVICE = config.get("device", "auto")

SAMPLE_RATE = config["sample_rate"]
WINDOW_SECONDS = config["window_seconds"]
STEP_SECONDS = config["step_seconds"]
BEAM_SIZE = config["beam_size"]
MAX_AUDIO_QUEUE = config["max_audio_queue"]
MAX_TEXT_QUEUE = config["max_text_queue"]

SILENCE_FLUSH_THRESHOLD = config.get("silence_flush_threshold", 0.5)
MIN_BUFFER_LEN_FOR_PUNCT_FLUSH = config.get("min_buffer_len_for_punct_flush", 60)
MIN_BUFFER_LEN_FOR_SILENCE_FLUSH = config.get("min_buffer_len_for_silence_flush", 20)
MAX_BUFFER_LEN = config.get("max_buffer_len", 120)

SAVE_TRANSCRIPT = config.get("save_transcript", True)
TRANSCRIPT_DIR = BASE_DIR / config.get("transcript_dir", "transcripts")

ui_config = config.get("ui", {})

WINDOW_ALPHA = ui_config.get("window_alpha", 0.8)
WINDOW_WIDTH = ui_config.get("window_width", 1000)
WINDOW_HEIGHT = ui_config.get("window_height", 120)
WINDOW_BOTTOM_MARGIN = ui_config.get("bottom_margin", 120)
WRAP_LENGTH = ui_config.get("wrap_length", 850)

BG_COLOR = ui_config.get("background_color", "black")
ENGLISH_TEXT_COLOR = ui_config.get("english_text_color", "#DDDDDD")
CHINESE_DEFAULT_COLOR = ui_config.get("chinese_default_color", "white")

ENGLISH_FONT_FAMILY = ui_config.get("english_font_family", "Segoe UI")
CHINESE_FONT_FAMILY = ui_config.get("chinese_font_family", "Microsoft JhengHei")
FONT_SIZE = ui_config.get("font_size", 18)

PLACEHOLDER_TEXT = ui_config.get("placeholder_text", "等待字幕...")

AUTHOR_NAME = ui_config.get("author_name", "Ken Lin")
AUTHOR_CONTACT = ui_config.get("author_contact", "bxlin@csie.io")
APP_VERSION = ui_config.get("app_version", "8.7.0")

print("[Startup] Initializing...\n")