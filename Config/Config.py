# Config.py

from pathlib import Path

# 共用模型目錄
MODELS_DIR = r"\\192.168.0.240\project\Ken_Lin\models"

MODEL_PATH_base = (
    rf"{MODELS_DIR}\Systranfaster-whisper-base"
)

MODEL_PATH_Translate = (
    rf"{MODELS_DIR}\nllb-200-distilled-600M"
)

# 檢查模型是否存在
for model_path in (
    MODEL_PATH_base,
    MODEL_PATH_Translate,
):
    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"模型不存在：{model_path}"
        )


SAMPLE_RATE = 16000

WINDOW_SECONDS = 4

STEP_SECONDS = 2

BEAM_SIZE = 3

MAX_AUDIO_QUEUE = 4

MAX_TEXT_QUEUE = 20

WORKER_COUNT = 1