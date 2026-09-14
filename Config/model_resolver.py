from pathlib import Path
import shutil
import sys
import os


def is_valid_model(path: Path, model_name: str, required_files_map: dict) -> bool:

    if not path.exists():
        return False

    if not any(path.iterdir()):
        return False

    required = required_files_map.get(model_name, ["config.json"])

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
    line = (
        f"  [{bar}] {percent:5.1f}%  "
        f"{format_size(copied)}/{format_size(total)}"
    )
    sys.stdout.write("\r\033[K" + line)  # \033[K 清除從游標到行尾的所有字元

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
    shutil.copystat(src, dst)


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


def resolve_model_path(
    model_name: str,
    remote_models_dir: str,
    local_models_dir: Path,
    required_files_map: dict,
) -> str:

    local_path = local_models_dir / model_name
    remote_path = Path(remote_models_dir) / model_name

    if is_valid_model(local_path, model_name, required_files_map):
        print(f"[Startup] Using local model: {model_name}")
        return str(local_path)

    print(f"[Startup] Model not found locally: {model_name}")
    print("[Startup] Copying from shared storage, please keep network stable...")

    local_models_dir.mkdir(parents=True, exist_ok=True)

    if local_path.exists():
        shutil.rmtree(local_path)

    if not remote_path.exists():
        raise FileNotFoundError(f"Model source not found: {remote_path}")

    copy_model_with_progress(remote_path, local_path)

    if not is_valid_model(local_path, model_name, required_files_map):
        raise RuntimeError(f"Model copy failed: {model_name}")

    print(f"[Startup] Done: {model_name}\n")
    return str(local_path)