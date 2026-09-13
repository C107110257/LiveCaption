from pathlib import Path
import json
import shutil
import sys
import os

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE = BASE_DIR / "config.json"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

REMOTE_MODELS_DIR = config["models_dir"]
LOCAL_MODELS_DIR = BASE_DIR / "models"


MODEL_REQUIRED_FILES = config.get("model_required_files", {})


def is_valid_model(path: Path, model_name: str):

    if not path.exists():
        return False

    if not any(path.iterdir()):
        return False

    required = MODEL_REQUIRED_FILES.get(model_name, ["config.json"])

    for file_name in required:
        if not (path / file_name).exists():
            return False

    return True


def get_dir_size(path: Path) -> int:
    """計算資料夾內所有檔案的總 bytes 數"""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for name in filenames:
            fp = Path(dirpath) / name
            if fp.exists():
                total += fp.stat().st_size
    return total


def format_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}TB"


def print_progress(copied: int, total: int, bar_len: int = 30):
    ratio = copied / total if total else 1
    ratio = min(ratio, 1.0)
    filled = int(bar_len * ratio)
    bar = "#" * filled + "-" * (bar_len - filled)
    percent = ratio * 100
    sys.stdout.write(
        f"\r  [{bar}] {percent:5.1f}%  "
        f"{format_size(copied)}/{format_size(total)}"
    )
    sys.stdout.flush()


def copy_file_with_progress(src: str, dst: str, progress_cb, chunk_size: int = 4 * 1024 * 1024):
    """自訂複製單一檔案，每讀寫一個 chunk 就回報一次進度"""
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        while True:
            chunk = fsrc.read(chunk_size)
            if not chunk:
                break
            fdst.write(chunk)
            progress_cb(len(chunk))
    shutil.copystat(src, dst)  # 保留檔案時間戳等 metadata,行為對齊 copy2


def copy_model_with_progress(remote_path: Path, local_path: Path):
    total_size = get_dir_size(remote_path)
    copied_size = {"value": 0}

    def on_chunk(n_bytes: int):
        copied_size["value"] += n_bytes
        print_progress(copied_size["value"], total_size)

    def copy_function(src, dst):
        copy_file_with_progress(src, dst, on_chunk)

    print_progress(0, total_size)
    try:
        shutil.copytree(remote_path, local_path, copy_function=copy_function)
    except Exception as e:
        print()
        print(f"[Startup] Copy failed: {e}")
        if local_path.exists():
            shutil.rmtree(local_path, ignore_errors=True)
        raise
    print()


def resolve_model_path(model_name):

    local_path = LOCAL_MODELS_DIR / model_name
    remote_path = Path(REMOTE_MODELS_DIR) / model_name

    if is_valid_model(local_path, model_name):
        print(f"[Startup] Using local model: {model_name}")
        return str(local_path)

    print(f"[Startup] Model not found locally: {model_name}")
    print("[Startup] Copying from shared storage, please keep network stable...")

    LOCAL_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if local_path.exists():
        shutil.rmtree(local_path)

    if not remote_path.exists():
        raise FileNotFoundError(f"Model source not found: {remote_path}")

    copy_model_with_progress(remote_path, local_path)

    if not is_valid_model(local_path, model_name):
        raise RuntimeError(f"Model copy failed: {model_name}")

    print(f"[Startup] Done: {model_name}\n")
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
        raise FileNotFoundError(f"Model does not exist: {model_path}")

print("[Startup] All models ready.")
print("[Startup] Initializing...\n")

SAMPLE_RATE = config["sample_rate"]
WINDOW_SECONDS = config["window_seconds"]
STEP_SECONDS = config["step_seconds"]
BEAM_SIZE = config["beam_size"]
MAX_AUDIO_QUEUE = config["max_audio_queue"]
MAX_TEXT_QUEUE = config["max_text_queue"]

def scaled_threads(ratio: float, total_cores: int, minimum: int = 1) -> int:
    """依比例換算執行緒數，至少保留 1 個，不超過總核心數"""
    count = round(total_cores * ratio)
    return max(minimum, min(count, total_cores))


TOTAL_CORES = os.cpu_count() or 4

WHISPER_CPU_THREADS = scaled_threads(
    config.get("whisper_cpu_threads_ratio", 0.4), TOTAL_CORES
)
TRANSLATOR_INTRA_THREADS = scaled_threads(
    config.get("translator_intra_threads_ratio", 0.3), TOTAL_CORES
)

print(f"[Startup] Detected {TOTAL_CORES} CPU cores.")
print(f"[Startup] whisper_cpu_threads = {WHISPER_CPU_THREADS}")
print(f"[Startup] translator_intra_threads = {TRANSLATOR_INTRA_THREADS}\n")

SILENCE_FLUSH_THRESHOLD = config.get("silence_flush_threshold", 0.5)
MIN_BUFFER_LEN_FOR_PUNCT_FLUSH = config.get("min_buffer_len_for_punct_flush", 60)
MIN_BUFFER_LEN_FOR_SILENCE_FLUSH = config.get("min_buffer_len_for_silence_flush", 20)
MAX_BUFFER_LEN = config.get("max_buffer_len", 120)