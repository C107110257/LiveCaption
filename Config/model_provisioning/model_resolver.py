from pathlib import Path
from typing import Optional
import time


from . common import is_valid_model, safe_rmtree
from . import huggingface_source
from . import shared_storage_source


def _swap_in(tmp_path: Path, final_path: Path) -> None:
    """
    用 rename 把下載好的暫存資料夾換成正式資料夾。
    rename 不需要遞迴走訪整個目錄樹，比直接 rmtree 更不容易被單一檔案的讀取鎖擋住。
    只有在舊資料夾真的連 rename 都失敗時，才退回用 safe_rmtree 硬刪。
    """
    trash_path: Optional[Path] = None

    if final_path.exists():
        trash_path = final_path.with_name(f"{final_path.name}.old_{int(time.time())}")
        try:
            final_path.rename(trash_path)
        except OSError:
            print(f"[Startup] Warning: rename failed, forcing delete of old folder: {final_path}")
            safe_rmtree(final_path)
            trash_path = None

    tmp_path.rename(final_path)

    if trash_path is not None:
        try:
            safe_rmtree(trash_path)
        except Exception as e:
            # 清舊資料夾失敗不影響這次結果，之後再手動清或下次啟動再試
            print(f"[Startup] Warning: could not clean up old folder {trash_path}: {e}")


def resolve_model_path(
    model_name: str,
    remote_models_dir: str,
    local_models_dir: Path,
    required_files_map: dict,
    huggingface_repos: Optional[dict] = None,
    prefer_huggingface: bool = True,
) -> str:
    """
    解析模型本機路徑：
    1. 本機已存在且完整 -> 直接使用
    2. 本機不存在/不完整 -> 優先嘗試 Hugging Face（若有設定對應 repo_id）
    3. Hugging Face 失敗或未設定 repo_id -> 備援使用 240 共用資料夾
    下載一律先進暫存資料夾，成功驗證後才用 rename 換入正式路徑。
    """

    local_path = local_models_dir / model_name

    if is_valid_model(local_path, model_name, required_files_map):
        print(f"[Startup] Using local model: {model_name}")
        return str(local_path)

    print(f"[Startup] Model not found locally: {model_name}")
    local_models_dir.mkdir(parents=True, exist_ok=True)

    tmp_path = local_models_dir / f"{model_name}.download_tmp"
    if tmp_path.exists():
        safe_rmtree(tmp_path)

    huggingface_repos = huggingface_repos or {}
    repo_id = huggingface_repos.get(model_name)

    if prefer_huggingface and repo_id:
        print(f"[Startup] Trying Hugging Face: {repo_id}")
        try:
            huggingface_source.fetch_from_huggingface(
                repo_id=repo_id,
                local_path=tmp_path,
                allow_patterns=required_files_map.get(model_name),
            )
            if is_valid_model(tmp_path, model_name, required_files_map):
                _swap_in(tmp_path, local_path)
                print(f"[Startup] Done (Hugging Face): {model_name}\n")
                return str(local_path)
            print("[Startup] Hugging Face download incomplete, falling back to shared storage...")
        except Exception as e:
            print(f"[Startup] Hugging Face download failed: {e}")
            print("[Startup] Falling back to shared storage...")

        if tmp_path.exists():
            safe_rmtree(tmp_path)

    print("[Startup] Copying from shared storage, please keep network stable...")
    shared_storage_source.fetch_from_network(remote_models_dir, model_name, tmp_path)

    if not is_valid_model(tmp_path, model_name, required_files_map):
        raise RuntimeError(f"Model copy failed: {model_name}")

    _swap_in(tmp_path, local_path)
    print(f"[Startup] Done (shared storage): {model_name}\n")
    return str(local_path)