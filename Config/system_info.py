import os


def get_total_cores() -> int:
    return os.cpu_count() or 4


def scaled_threads(ratio: float, total_cores: int, minimum: int = 1) -> int:
    """依比例換算執行緒數，至少保留 1 個，不超過總核心數"""
    count = round(total_cores * ratio)
    return max(minimum, min(count, total_cores))


def get_thread_counts(config: dict) -> tuple[int, int]:
    """回傳 (whisper_threads, translator_threads)"""
    total_cores = get_total_cores()

    whisper_threads = scaled_threads(
        config.get("whisper_cpu_threads_ratio", 0.4), total_cores
    )
    translator_threads = scaled_threads(
        config.get("translator_intra_threads_ratio", 0.3), total_cores
    )

    print(f"[Startup] Detected {total_cores} CPU cores.")
    print(f"[Startup] whisper_cpu_threads = {whisper_threads}")
    print(f"[Startup] translator_intra_threads = {translator_threads}\n")

    return whisper_threads, translator_threads