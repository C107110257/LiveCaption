from pathlib import Path
import shutil
import os

from .progress import ProgressReporter


def get_dir_size(path: Path) -> int:
    """計算資料夾內所有檔案的總 bytes 數"""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for name in filenames:
            fp = Path(dirpath) / name
            if fp.exists():
                total += fp.stat().st_size
    return total


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
    reporter = ProgressReporter(total_size)

    def copy_function(src, dst):
        copy_file_with_progress(src, dst, reporter.update)

    try:
        shutil.copytree(remote_path, local_path, copy_function=copy_function)
    except Exception as e:
        reporter.close()
        print(f"[Startup] Copy failed: {e}")
        if local_path.exists():
            shutil.rmtree(local_path, ignore_errors=True)
        raise
    reporter.close()


def fetch_from_network(remote_models_dir: str, model_name: str, local_path: Path) -> None:
    """從 240 共用資料夾複製模型到本機，作為備援方案"""
    remote_path = Path(remote_models_dir) / model_name

    if not remote_path.exists():
        raise FileNotFoundError(f"Model source not found: {remote_path}")

    copy_model_with_progress(remote_path, local_path)