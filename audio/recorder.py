import numpy as np
import soundcard as sc

from collections import deque
from queue import Full

from config.settings import SAMPLE_RATE, WINDOW_SECONDS, STEP_SECONDS


EXCLUDED_KEYWORDS = ["display audio", "digital output", "s/pdif", "spdif"]


class AudioRecorder:

    def __init__(self, queue, status_callback=None):
        """
        status_callback: 選填, callable(is_ready: bool, message: str) -> None
        用來讓外部(UI)即時知道錄音裝置狀態變化,不傳的話就只能靠 device_ready 旗標被動查詢
        """
        self.queue = queue
        self.status_callback = status_callback
        self.device_ready = False

        self.mic = self._find_working_loopback_device()
        self.device_ready = self.mic is not None
        self._notify(self.device_ready)

    def _notify(self, is_ready: bool, message: str = ""):
        if self.status_callback is not None:
            try:
                self.status_callback(is_ready, message)
            except Exception as e:
                print(f"[Audio][WARNING] status_callback 執行失敗: {e}")

    def _test_device_has_signal(self, speaker, test_seconds: float = 1.2) -> bool:
        try:
            mic = sc.get_microphone(id=speaker.id, include_loopback=True)
            with mic.recorder(samplerate=SAMPLE_RATE) as recorder:
                data = recorder.record(numframes=int(SAMPLE_RATE * test_seconds))
            peak = np.abs(data).max()
            return peak > 1e-5
        except Exception:
            return False

    def _find_working_loopback_device(self):
        speakers = sc.all_speakers()

        try:
            default = sc.default_speaker()
            candidates = [default] + [s for s in speakers if s.id != default.id]
        except Exception:
            candidates = speakers

        valid_candidates = [
            spk for spk in candidates
            if not any(k in spk.name.lower() for k in EXCLUDED_KEYWORDS)
        ]

        if not valid_candidates:
            print("[Audio][WARNING] 沒有找到符合條件的裝置類型,改用全部裝置當候選")
            valid_candidates = candidates

        print("[Audio] 開始偵測可用的 loopback 裝置...")

        for spk in valid_candidates:
            print(f"[Audio]   測試中: {spk.name} ...")
            if self._test_device_has_signal(spk):
                print(f"[Audio] 已選用: {spk.name}(偵測到訊號)")
                mic = self._try_get_microphone(spk)
                if mic is not None:
                    return mic
            else:
                print(f"[Audio]   無訊號: {spk.name}")

        print("[Audio][WARNING] 啟動時所有裝置皆無訊號(可能尚未開始播放聲音),嘗試退回可用裝置...")

        for spk in valid_candidates:
            mic = self._try_get_microphone(spk)
            if mic is not None:
                print(f"[Audio][WARNING] 退回使用: {spk.name}")
                return mic

        self._print_diagnostics()
        print("[Audio][ERROR] 找不到任何可建立的 loopback 裝置,錄音將無法啟動,程式繼續執行但不會有字幕產生")
        return None

    def _try_get_microphone(self, speaker):
        try:
            return sc.get_microphone(id=speaker.id, include_loopback=True)
        except Exception as e:
            print(f"[Audio]   無法建立裝置 {speaker.name}: {e}")
            return None

    def _print_diagnostics(self):
        print("=" * 50)
        print("[Audio] 所有偵測到的輸出裝置:")
        for spk in sc.all_speakers():
            print(f"  - id={spk.id}  name={spk.name}")
        print("=" * 50)

    def run(self):

        if self.mic is None:
            print("[Audio][ERROR] 沒有可用的錄音裝置,run() 直接返回,不會有音訊被處理")
            return

        buffer = deque(maxlen=WINDOW_SECONDS // STEP_SECONDS)
        silent_chunks = 0

        try:
            with self.mic.recorder(samplerate=SAMPLE_RATE) as recorder:

                while True:

                    chunk = recorder.record(numframes=SAMPLE_RATE * STEP_SECONDS)
                    buffer.append(chunk)

                    if len(buffer) < buffer.maxlen:
                        continue

                    audio = np.concatenate(list(buffer), axis=0)
                    volume = np.abs(audio).mean()

                    if volume < 0.001:
                        silent_chunks += 1
                        if silent_chunks == 10:
                            print("[Audio][WARNING] 已持續偵測到靜音,請確認該輸出裝置是否正在播放聲音")
                        continue

                    silent_chunks = 0

                    try:
                        self.queue.put_nowait(audio)
                    except Full:
                        try:
                            self.queue.get_nowait()
                        except Exception:
                            pass
                        self.queue.put_nowait(audio)

        except Exception as e:
            self.device_ready = False
            self._notify(False, f"錄音中斷: {e}")
            print(f"[Audio][ERROR] 錄音過程中發生例外,錄音已停止: {e}")