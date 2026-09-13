import sys
import numpy as np
import soundcard as sc

from collections import deque
from queue import Full

from Config.Config import SAMPLE_RATE, WINDOW_SECONDS, STEP_SECONDS


# 這些裝置類型常見不支援 loopback 錄音,自動排除,不用花時間去試
EXCLUDED_KEYWORDS = ["display audio", "digital output", "s/pdif", "spdif"]


class AudioRecorder:

    def __init__(self, queue):
        self.queue = queue
        self.mic = self._find_working_loopback_device()

    def _test_device_has_signal(self, speaker, test_seconds: float = 1.2) -> bool:
        """實際錄一小段,確認這個裝置真的能透過 loopback 抓到聲音"""
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

        # 過濾掉已知不支援 loopback 的裝置類型,保留下來的當作候選清單
        valid_candidates = [
            spk for spk in candidates
            if not any(k in spk.name.lower() for k in EXCLUDED_KEYWORDS)
        ]

        # 連篩選後的候選清單都是空的(極端情況),
        # 就不篩選了,把所有裝置都當候選,絕不讓程式在這裡掛掉
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

        # 沒有任何裝置測到訊號(可能是還沒開始播放聲音),
        # 依序嘗試候選清單裡每一個裝置,選第一個能成功建立的,不報錯
        print("[Audio][WARNING] 啟動時所有裝置皆無訊號(可能尚未開始播放聲音),嘗試退回可用裝置...")

        for spk in valid_candidates:
            mic = self._try_get_microphone(spk)
            if mic is not None:
                print(f"[Audio][WARNING] 退回使用: {spk.name}")
                return mic

        # 連退回都失敗,印出完整診斷資訊,但仍然不中斷程式,
        # 回傳 None,交給 run() 處理成「暫停錄音、持續重試」而不是崩潰
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
            print(f"[Audio][ERROR] 錄音過程中發生例外,錄音已停止: {e}")