from queue import Queue
import threading

from Config.Config import MAX_AUDIO_QUEUE

audio_queue = Queue(maxsize=MAX_AUDIO_QUEUE)
english_queue = Queue()
chinese_queue = Queue()

translator = None

translator_ready_event = threading.Event()
whisper_ready_event = threading.Event()