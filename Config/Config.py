from pathlib import Path
import json
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE = BASE_DIR / "config.json"

with open(
    CONFIG_FILE,
    "r",
    encoding="utf-8"
) as f:
    config = json.load(f)

MODELS_DIR = config["models_dir"]

whisper_model = str(
    Path(MODELS_DIR)
    / config["whisper_model"]
)

translate_model = str(
    Path(MODELS_DIR)
    / config["translate_model"]
)

translate_model_ct2 = str(
    Path(MODELS_DIR)
    / config["translate_model_ct2"]
)

for model_path in (
    whisper_model,
    translate_model,
    translate_model_ct2,
):
    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"模型不存在：{model_path}"
        )

SAMPLE_RATE = config["sample_rate"]
WINDOW_SECONDS = config["window_seconds"]
STEP_SECONDS = config["step_seconds"]
BEAM_SIZE = config["beam_size"]
MAX_AUDIO_QUEUE = config["max_audio_queue"]
MAX_TEXT_QUEUE = config["max_text_queue"]
WORKER_COUNT = config["worker_count"]

WHISPER_CPU_THREADS = config.get("whisper_cpu_threads", 4)
TRANSLATOR_INTRA_THREADS = config.get("translator_intra_threads", 4)