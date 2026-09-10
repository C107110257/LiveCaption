# verify_tokenizer.py，暫時獨立測試用
from transformers import AutoTokenizer
import sentencepiece as spm
import re

translate_model = r"\\192.168.0.240\project\Ken_Lin\models\nllb-200-distilled-1.3B"

old_tokenizer = AutoTokenizer.from_pretrained(translate_model, src_lang="eng_Latn")
sp = spm.SentencePieceProcessor(model_file=f"{translate_model}\\sentencepiece.bpe.model")

test_sentences = [
    "Hello, how are you?",
    "The Strait of Hormuz remains a flashpoint.",
    "Iran's Supreme National Security Council issued a statement.",
    "9 million barrels of oil are being transferred.",
    "Sanctions imposed on Iran continue to bite.",
]

for text in test_sentences:
    old_tokens = old_tokenizer.convert_ids_to_tokens(old_tokenizer.encode(text))

    normalized = re.sub(r"\s+", " ", text).strip()
    new_tokens = ["eng_Latn"] + sp.encode(normalized, out_type=str) + ["</s>"]

    match = "✅" if old_tokens == new_tokens else "❌"
    print(f"{match} {text}")
    if old_tokens != new_tokens:
        print(f"   OLD: {old_tokens}")
        print(f"   NEW: {new_tokens}")