import os
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"


import time
import ctranslate2
from transformers import AutoTokenizer
from config.settings import *



class OfflineTranslator:

    def __init__(self, status_callback=None):

        self.status_callback = status_callback

        if self.status_callback:
            self.status_callback(
                "翻譯模型載入中...", "Loading Translator...", "#FFA500"
            )

        start = time.perf_counter()

        self.tokenizer = AutoTokenizer.from_pretrained(
            translate_model,
            src_lang="eng_Latn",
        )

        self.translator = ctranslate2.Translator(
            translate_model_ct2,
            device=DEVICE,
            inter_threads=1,
            intra_threads=TRANSLATOR_INTRA_THREADS,
        )

        print(f"Translator Loaded: {time.perf_counter() - start:.2f}s")

        if self.status_callback:
            self.status_callback(
                "翻譯模型預熱中...", "Warming Translator...", "#FFA500"
            )

        start = time.perf_counter()

        self.translate("Hello")

        print(f"Translator Ready: {time.perf_counter() - start:.2f}s")

    def translate(self, text):

        source_tokens = self.tokenizer.convert_ids_to_tokens(
            self.tokenizer.encode(text)
        )

        target_prefix = [["zho_Hant"]]

        results = self.translator.translate_batch(
            [source_tokens],
            target_prefix=target_prefix,
            max_decoding_length=128,
            beam_size=4,
        )

        target_tokens = results[0].hypotheses[0][1:]
        target_ids = self.tokenizer.convert_tokens_to_ids(target_tokens)

        return self.tokenizer.decode(
            target_ids,
            skip_special_tokens=True,
        )