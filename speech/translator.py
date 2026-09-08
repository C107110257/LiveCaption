import time

from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
)

from Config.Config import MODEL_PATH_Translate


class OfflineTranslator:

    def __init__(self, status_callback=None):

        self.status_callback = status_callback

        print(f"Translator Model: {MODEL_PATH_Translate}")

        if self.status_callback:
            self.status_callback(
                "翻譯模型載入中...",
                "Loading Translator...",
                "#FFA500"
            )

        start = time.perf_counter()

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_PATH_Translate
        )

        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_PATH_Translate
        )

        self.model.eval()

        print(
            f"Translator Loaded: "
            f"{time.perf_counter() - start:.2f}s"
        )

        if self.status_callback:
            self.status_callback(
                "翻譯模型預熱中...",
                "Warming Translator...",
                "#FFA500"
            )

        start = time.perf_counter()

        self.translate("Hello")

        print(
            f"Translator Ready: "
            f"{time.perf_counter() - start:.2f}s"
        )

    def translate(self, text):

        inputs = self.tokenizer(
            text,
            return_tensors="pt"
        )

        translated_tokens = self.model.generate(
            **inputs,
            forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(
                "zho_Hant"
            ),
        )

        return self.tokenizer.decode(
            translated_tokens[0],
            skip_special_tokens=True
        )