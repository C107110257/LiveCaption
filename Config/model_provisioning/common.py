from pathlib import Path
import os
import shutil
import stat
import time


def safe_rmtree(path: Path, retries: int = 5, delay: float = 1.0) -> None:
    """
    刪除資料夾，處理常見的權限/鎖定問題：
    - Google Drive / OneDrive 等雲端同步軟體背景鎖住檔案
    - 檔案被標成唯讀
    失敗時會清除唯讀屬性並重試幾次，最後仍失敗才拋出例外。
    """
    if not path.exists():
        return

    def on_error(func, target_path, exc_info):
        try:
            os.chmod(target_path, stat.S_IWRITE)
            func(target_path)
        except Exception:
            pass

    last_error: Exception | None = None
    for attempt in range(retries):
        if not path.exists():
            return
        try:
            shutil.rmtree(path, onerror=on_error)
            if not path.exists():
                return
        except Exception as e:
            last_error = e
        time.sleep(delay)

    raise PermissionError(
        f"無法刪除資料夾（可能被雲端同步軟體或其他程式鎖住，"
        f"請先關閉相關程式或暫停同步後再試一次）: {path}"
    ) from last_error


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