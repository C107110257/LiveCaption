# Live Caption

即時英文語音辨識 + 中文翻譯的桌面字幕疊加工具。擷取系統播放的聲音（例如視訊會議、線上課程、Youtube 影片），即時轉成英文文字並翻譯成中文，以半透明字幕視窗顯示在畫面上。

![Demo：一邊播放 NASA 直播，一邊即時顯示英文辨識與中文翻譯字幕](./assets/demo.png)

```
英文語音 → Whisper 轉錄 → NLLB 翻譯 → 半透明字幕視窗
```

## 功能特色

- **系統音訊擷取**：透過 loopback 裝置擷取電腦正在播放的聲音，不需要外接麥克風或額外錄音設備
- **即時語音轉文字**：使用 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)（distil-whisper medium.en，CTranslate2 加速）
- **即時翻譯**：使用 Meta 的 [NLLB-200](https://github.com/facebookresearch/fairseq/tree/nllb) distilled 1.3B 模型（CTranslate2 轉檔版），將辨識出的英文即時翻成繁體中文
- **半透明疊加字幕視窗**：可自訂透明度、字型、字級、視窗大小與位置
- **逐字稿自動存檔**：每次執行時，英文原文與中文翻譯的配對會即時寫入 `transcripts/` 資料夾下的 txt 檔（檔名帶啟動時間），可用 `config.json` 的 `save_transcript` 開關
- **模型自動就緒**：程式啟動時自動檢查本機模型是否完整，缺少或不完整時會自動下載（優先 Hugging Face，備援內部共用儲存），不需要手動準備模型

## 環境需求

- Windows（音訊擷取使用 loopback 裝置，目前僅支援 Windows）
- Python 3.12+
- 建議有獨立顯示卡可加速推論（CPU 也可執行，速度較慢）

## 安裝

```powershell
git clone <你的 repo 網址>
cd test_audio
pip install -r requirements.txt
copy config.example.json config.json
```

複製出來的 `config.json` 裡的 `models_dir` 是內部共用儲存路徑（一般使用者用不到，`prefer_huggingface: true` 時會直接跳過，見下方「模型準備」）。

主要相依套件：

| 套件 | 用途 |
|---|---|
| `faster_whisper` | 語音辨識（Whisper 的 CTranslate2 加速版） |
| `ctranslate2` | 執行 CTranslate2 格式模型的推論引擎（faster-whisper 與翻譯模型都依賴它） |
| `transformers` | 載入 NLLB tokenizer，將文字轉成模型看得懂的 token |
| `huggingface_hub` | 從 Hugging Face 自動下載模型 |
| `soundcard` | 擷取系統播放中的音訊（loopback 錄音） |
| `numpy` | 音訊資料的數值運算 |
| `tqdm` | 共用進度條模組（`config/model_provisioning/progress.py`）依賴的顯示元件 |

## 模型準備

第一次執行時，程式會依 `config.json` 裡的設定，依序嘗試：

1. **本機是否已有完整模型** → 有的話直接使用
2. **Hugging Face**（依 `huggingface_repos` 對照表下載，全部公開，不需要 token）
3. **內部共用儲存**（備援方案，僅限公司內網環境可用）

需要用到的模型：

| 模型 | 用途 | Hugging Face repo |
|---|---|---|
| faster-distil-whisper-medium.en | 語音辨識 | [`Systran/faster-distil-whisper-medium.en`](https://huggingface.co/Systran/faster-distil-whisper-medium.en) |
| nllb-200-distilled-1.3B | 翻譯用 tokenizer | [`facebook/nllb-200-distilled-1.3B`](https://huggingface.co/facebook/nllb-200-distilled-1.3B) |
| nllb-200-distilled-1.3B-ct2 | 翻譯模型（CTranslate2 轉檔版） | [`Pohsiu/nllb-200-distilled-1.3B-ct2`](https://huggingface.co/Pohsiu/nllb-200-distilled-1.3B-ct2) |

三個模型都是公開 repo，`git clone` 後直接執行即可自動下載，不需要申請任何權限或準備 token。

### 自行轉換模型（可選）

如果你想自己準備一份 ct2 版本的翻譯模型（例如想換量化精度、或想轉其他語言對）：

```bash
pip install ctranslate2 transformers
ct2-transformers-converter --model facebook/nllb-200-distilled-1.3B \
    --output_dir nllb-200-distilled-1.3B-ct2 \
    --quantization int8
```

轉檔完成後上傳到你自己的 Hugging Face 帳號，並把 `config.json` 裡 `huggingface_repos.nllb-200-distilled-1.3B-ct2` 改成你自己的 repo_id。

## 使用方式

```powershell
python main.py
```

啟動後：

1. 程式會先確認/下載模型，並印出目前使用的執行緒配置
2. 自動偵測可用的系統音訊 loopback 裝置
3. 顯示半透明字幕視窗，播放中的英文語音會即時被辨識並翻譯成中文顯示
4. 若 `save_transcript` 為開（預設開），每組翻譯結果會同步寫入 `transcripts/transcript_<啟動時間>.txt`

關閉視窗即可結束程式。

## 設定檔（config.json）

| 欄位 | 說明 |
|---|---|
| `models_dir` | 內部共用儲存路徑（備援下載來源） |
| `huggingface_repos` | 各模型對應的 Hugging Face repo_id |
| `prefer_huggingface` | 是否優先從 Hugging Face 下載（預設 `true`） |
| `sample_rate` / `window_seconds` / `step_seconds` | 音訊擷取的取樣率與切窗參數 |
| `beam_size` | Whisper 解碼的 beam search 寬度，越大越準但越慢 |
| `whisper_cpu_threads_ratio` / `translator_intra_threads_ratio` | 依 CPU 核心數比例配置各模型的執行緒數量 |
| `save_transcript` | 是否把每組英中翻譯結果存成 txt（預設 `true`） |
| `transcript_dir` | 逐字稿存檔資料夾（預設 `transcripts`，已加入 `.gitignore`） |
| `ui.*` | 字幕視窗外觀（透明度、大小、字型、顏色、位置） |

完整欄位請直接參考專案根目錄的 `config.json`。

## 打包成執行檔（可選）

```powershell
.\build.ps1
```

會依目前登入帳號的桌面路徑，用 PyInstaller 打包成獨立執行檔（`--onedir` 模式，exe 旁邊會有一個 `_internal` 資料夾，這是正常的，不建議改成單一 exe，詳見程式碼註解）。內部共用儲存的發布步驟若偵測不到該路徑會自動跳過，不影響本機 build 是否成功。

## 專案結構

```
test_audio/
├── main.py                      # 程式進入點
├── config.json                  # 設定檔
├── config/
│   ├── settings.py              # 讀取設定、解析模型路徑
│   ├── json_loader.py
│   ├── system_info.py           # CPU 執行緒配置
│   └── model_provisioning/      # 模型取得邏輯
│       ├── model_resolver.py    # 統一入口：本機優先 → HF → 共用儲存備援
│       ├── huggingface_source.py
│       ├── shared_storage_source.py
│       ├── common.py            # 模型驗證、安全刪除
│       └── progress.py          # 共用進度條
├── audio/
│   └── recorder.py              # 系統音訊 loopback 擷取
├── speech/
│   ├── transcriber.py           # Whisper 轉錄
│   └── translator.py            # NLLB 翻譯
├── pipeline/
│   ├── state.py                 # 跨執行緒共用的佇列與事件
│   ├── transcript_logger.py     # 英中翻譯配對寫入 txt
│   ├── whisper_worker.py
│   ├── translator_worker.py
│   └── ui_worker.py
├── ui/
│   └── caption_window.py        # 半透明字幕視窗
├── transcripts/                 # 逐字稿存檔位置（.gitignore）
└── models/                      # 下載後的模型存放位置（.gitignore）
```

## 致謝 / 使用的模型

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) / [distil-whisper](https://github.com/huggingface/distil-whisper)
- [NLLB-200](https://ai.meta.com/research/no-language-left-behind/)（Meta AI，CC-BY-NC 4.0）
- [CTranslate2](https://github.com/OpenNMT/CTranslate2)

## License

本專案採用 [MIT License](./LICENSE)。

> 注意：翻譯模型 [NLLB-200](https://ai.meta.com/research/no-language-left-behind/) 本身受 **CC-BY-NC-4.0** 授權（僅限非商業用途），與本專案 code 的授權是分開的兩件事——你可以自由使用/修改本專案的程式碼，但若商業使用，翻譯模型部分需另行取得授權或替換成其他授權更寬鬆的翻譯模型。

## 作者

Ken Lin