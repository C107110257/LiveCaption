import re
import time
from pathlib import Path

import ctranslate2
import sentencepiece as spm

from Config.Config import *


SRC_LANG = "eng_Latn"
TGT_LANG = "zho_Hant"
EOS_TOKEN = "</s>"

_SPACE_RE = re.compile(r"\s+")


class OfflineTranslator:

    def __init__(self, status_callback=None):

        self.status_callback = status_callback

        if self.status_callback:
            self.status_callback(
                "翻譯模型載入中...", "Loading Translator...", "#FFA500"
            )

        start = time.perf_counter()

        sp_model_path = str(
            Path(translate_model) / "sentencepiece.bpe.model"
        )
        self.sp = spm.SentencePieceProcessor(model_file=sp_model_path)

        self.translator = ctranslate2.Translator(
            translate_model_ct2,
            device="cpu",
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

    def _encode(self, text):
        text = _SPACE_RE.sub(" ", text).strip()
        pieces = self.sp.encode(text, out_type=str)
        return [SRC_LANG] + pieces + [EOS_TOKEN]

    def _decode(self, pieces):
        pieces = [
            p for p in pieces
            if p not in (SRC_LANG, TGT_LANG, EOS_TOKEN, "<s>", "<pad>", "<unk>")
        ]
        return self.sp.decode(pieces)

    def translate(self, text):

        source_tokens = self._encode(text)

        target_prefix = [[TGT_LANG]]

        results = self.translator.translate_batch(
            [source_tokens],
            target_prefix=target_prefix,
            max_decoding_length=128,
            beam_size=4,
        )

        target_tokens = results[0].hypotheses[0][1:]

        return self._decode(target_tokens)