from pathlib import Path
import json
import shutil
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE = BASE_DIR / "config.json"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

REMOTE_MODELS_DIR = config["models_dir"]
LOCAL_MODELS_DIR = BASE_DIR / "models"


def is_valid_model(path: Path):

    if not path.exists():
        return False

    if not any(path.iterdir()):
        return False

    required = ["config.json"]

    name = path.name.lower()

    if (
        "whisper" in name
        or "ct2" in name
    ):
        required.append("model.bin")

    for file_name in required:

        if not (path / file_name).exists():
            return False

    return True


def resolve_model_path(model_name):

    local_path = LOCAL_MODELS_DIR / model_name
    remote_path = Path(REMOTE_MODELS_DIR) / model_name

    if is_valid_model(local_path):
        return str(local_path)

    print(f"Copy model: {model_name}")

    LOCAL_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if local_path.exists():
        shutil.rmtree(local_path)

    if not remote_path.exists():
        raise FileNotFoundError(f"找不到模型來源: {remote_path}")

    shutil.copytree(remote_path, local_path)

    if not is_valid_model(local_path):
        raise RuntimeError(f"模型複製失敗: {model_name}")
    return str(local_path)


whisper_model = resolve_model_path(config["whisper_model"])
translate_model = resolve_model_path(config["translate_model"])
translate_model_ct2 = resolve_model_path(config["translate_model_ct2"])

for model_path in (
    whisper_model,
    translate_model,
    translate_model_ct2,
):
    if not Path(model_path).exists():
        raise FileNotFoundError(f"模型不存在：{model_path}")

SAMPLE_RATE = config["sample_rate"]
WINDOW_SECONDS = config["window_seconds"]
STEP_SECONDS = config["step_seconds"]
BEAM_SIZE = config["beam_size"]
MAX_AUDIO_QUEUE = config["max_audio_queue"]
MAX_TEXT_QUEUE = config["max_text_queue"]

WHISPER_CPU_THREADS = config.get("whisper_cpu_threads", 4)
TRANSLATOR_INTRA_THREADS = config.get("translator_intra_threads", 4)

SILENCE_FLUSH_THRESHOLD = config.get("silence_flush_threshold", 0.5)
MIN_BUFFER_LEN_FOR_PUNCT_FLUSH = config.get("min_buffer_len_for_punct_flush", 60)
MIN_BUFFER_LEN_FOR_SILENCE_FLUSH = config.get("min_buffer_len_for_silence_flush", 20)
MAX_BUFFER_LEN = config.get("max_buffer_len", 120)
