# OCR 模型下载地址与说明

本文档汇总吏部支持的 OCR 引擎、模型下载地址与平台兼容性说明。
**所有模型均需用户在软件「设置 → 本地 OCR 模型」中导入或按提示安装依赖。**

---

## 一、本地 OCR 引擎

### 1. Tesseract（保底引擎，推荐离线使用）

- 项目：https://github.com/tesseract-ocr/tesseract
- 中文语言包：
  - 简体：https://github.com/tesseract-ocr/tessdata/blob/main/chi_sim.traineddata
  - 繁体：https://github.com/tesseract-ocr/tessdata/blob/main/chi_tra.traineddata
  - 最佳精度：https://github.com/tesseract-ocr/tessdata_best
- 安装：`sudo apt install tesseract-ocr tesseract-ocr-chi-sim`

### 2. PP-OCRv5（百度 PaddleOCR）

- 项目：https://github.com/PaddlePaddle/PaddleOCR
- 模型库：https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/model_list.md
- 安装：`pip install paddlepaddle paddleocr`
- 说明：PaddleOCR 3.x 默认即 PP-OCRv5，中文与工整手写表现优秀，CPU 可跑。

### 3. PaddleOCR-VL-0.9B（百度多模态文档解析）

- 模型：https://huggingface.co/PaddlePaddle/PaddleOCR-VL-0.9B
- 安装：`pip install "paddleocr[doc-parser]"`
- 说明：擅长复杂版面、表格、公式，可输出结构化 Markdown/JSON。

### 4. ModernVBERT（社区版）

- 模型：https://huggingface.co/ModernVBERT/ModernVBERT-250M
- 说明：250M 文档视觉语言模型，偏向文档理解/检索；需 transformers 权重。
  下载后放入 `~/.libu/models/<目录名含 vbert>`。

### 5. HunyuanOCR（腾讯混元）

- 项目：https://github.com/Tencent-Hunyuan/HunyuanOCR
- API：https://cloud.tencent.com/product/hunyuan
- 说明：可本地部署或通过混元视觉接口调用，本项目默认走接口（需 API Key）。

### 6. MonkeyOCR

- 项目：https://github.com/Yuliang-Liu/MonkeyOCR
- 说明：结构识别 + 识别两阶段方案。权重下载后放入 `~/.libu/models/MonkeyOCR`。

### 7. DeepSeek-OCR

- 项目：https://github.com/deepseek-ai/DeepSeek-OCR
- 权重：见项目 README（Hugging Face）。放入 `~/.libu/models/` 后本地推理；
  或在设置中填写 DeepSeek API Key 走接口。
- 说明：端到端 OCR，支持中英文 + 表格 + 公式。

### 8. 自定义 ONNX 模型（RapidOCR）与 PaddleOCR 一键导入包（重点）

- RapidOCR：https://github.com/RapidAI/RapidOCR
- 安装：`pip install rapidocr-onnxruntime onnxruntime`
- **吏部已随附现成的一键导入包**：`OCR Model/paddleocr_ppocrv5.zip`

  **使用方法**：
  1. 打开吏部 →「设置」→「本地 OCR 模型」→「导入模型 zip」；
  2. 选择 `OCR Model/paddleocr_ppocrv5.zip`；
  3. 在「各功能的 OCR 模型」中选择「自定义本地模型 (ONNX)」（需已安装
     `rapidocr-onnxruntime` 与 `onnxruntime`）。

  **压缩包内容**（PP-OCRv5 mobile，体积小、CPU 可跑、中英文通用）：

  ```
  paddleocr_ppocrv5/
  ├── ppocrv5-mobile-det.onnx   # 文本检测（约 4.7 MB）
  ├── ppocrv5-mobile-rec.onnx   # 文本识别（约 16 MB）
  ├── ppocrv5-cls.onnx          # 文本行方向分类（约 0.6 MB）
  └── ppocrv5_dict.txt          # 识别字典（必须与 rec 模型配套）
  ```

  **以后如何自己配置**：
  - 只要是 PP-OCR 系列的 ONNX 模型，把 `det` / `rec` / `cls` 三个 `.onnx`
    放进同一个目录，文件名分别包含 `det`、`rec`、`cls` 关键字；
  - 再放入一个包含识别字符集的 `*dict*.txt` 或 `*keys*.txt`（v4 与 v5 的
    字典不同，务必配套），一起打成 zip；
  - 在软件中导入该 zip，选择「自定义本地模型 (ONNX)」即可。
  - 重新构建随附包：`bash scripts/build-paddleocr-model.sh`

  **模型来源**：
  - PP-OCRv5 ONNX（推荐）：https://huggingface.co/bukuroo/PPOCRv5-ONNX
  - 官方 PP-OCRv5 权重（Paddle 格式）：https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_det
  - 更多 ONNX：https://huggingface.co/SWHL/RapidOCR

  > 提示：本包使用 PP-OCRv5 字典 `ppocrv5_dict.txt`。若自行替换成 PP-OCRv4
  > 的 rec 模型，请同时替换为 v4 字典（`ppocr_keys_v1.txt`），否则识别会乱码。

### 9. GLM OCR / 智谱视觉模型

- 智谱开放平台（API）：https://open.bigmodel.cn/
- 开源视觉模型：
  - GLM-4V-9B：https://huggingface.co/THUDM/glm-4v-9b
  - GLM-4.1V-Thinking：https://huggingface.co/THUDM/GLM-4.1V-9B-Thinking
- 说明：GLM 系列以多模态 API 使用为主；如官方发布独立 `GLM-OCR` 权重，
  请以智谱官方仓库 https://huggingface.co/zai-org 为准。

### 10. OpenAI OCR

- OpenAI **未开源**独立 OCR 模型。请通过视觉 API 使用：
  - 文档：https://platform.openai.com/docs/guides/vision
  - 模型：`gpt-4o` / `gpt-4.1` / `gpt-4o-mini` 等
- 说明：在软件「设置 → 大模型 API」中填入 API Key 后即可作为视觉 OCR 使用。
  （本版本的内置大模型列表可在 `llm_backends.py` 中按需扩展 OpenAI 兼容项。）

### 11. 微信 OCR（重点）

- 压缩包：`OCR Model/wechat_ocr.zip`
- 来源：从微信 Linux 客户端安装包提取。
- 内容：

```
wechat_ocr_pkg/
├── wxocr                       # 启动器（ELF，按平台编译）
├── libwxocr.so                 # 运行库（Linux x86_64）
└── ocr_model/                  # .xnet 权重 + 字符集
    ├── text_det_fp16_v2.xnet
    ├── text_rec_zh13562_fp16_v2.xnet
    ├── paragraph_det_fp16_v2.xnet
    ├── charset_zh13562.txt
    └── ...
```

**常见问题：**

1. **是否只提取 `ocr_model` 就够了？**
   不够。`ocr_model` 只是权重，还需要对应平台的 `wxocr` + `libwxocr.so` 运行库。
   本 zip 已包含 x86_64 Linux 版本。

2. **Windows 和 Linux 的模型通用吗？**
   `.xnet` **权重与字符集跨平台通用**；但 `wxocr` / `libwxocr.so`（运行库）按平台编译，不通用。
   Windows 需使用 Windows 版微信的对应运行库。

3. **为什么运行时报缺少 `libmmmojo.so`？**
   `wxocr` 依赖微信客户端的 Mojo 运行时。解决方案：
   - 安装微信 Linux 客户端，然后在设置中把 `/opt/wechat` 加入「微信运行库目录」；
   - 或在设置中填写自定义命令模板。
   注意：这是腾讯专有组件，本项目**不分发**。

---

## 二、在线 OCR 引擎（数据会上传，含隐私风险）

| 引擎 | 地址 | 说明 |
| --- | --- | --- |
| OCR.space | https://ocr.space/ | 免费额度，注册获取 API Key |
| 百度云 OCR | https://cloud.baidu.com/product/ocr | 通用文字识别，需 API Key + Secret |

## 三、大模型 API

| 提供商 | 地址 |
| --- | --- |
| DeepSeek | https://platform.deepseek.com/ |
| 智谱 GLM | https://open.bigmodel.cn/ |
| Kimi | https://platform.moonshot.cn/ |
| MiniMax | https://www.minimaxi.com/ |
| 阶跃星辰 | https://platform.stepfun.com/ |
| Qwen（通义千问） | https://dashscope.aliyun.com/ |
| 零一万物 | https://platform.lingyiwanwu.com/ |
| 英伟达 NIM | https://build.nvidia.com/ |
| 腾讯混元 | https://cloud.tencent.com/product/hunyuan |

## 四、Agent / 本地 AI 助手

| 助手 | 默认地址 |
| --- | --- |
| OpenCode | http://localhost:4096 |
| DeepSeek Harness | http://localhost:8000 |
| Claude Code | http://localhost:3000 |
| Codex | http://localhost:3001 |
| Cherry Studio | http://localhost:23333 |
| Ollama | http://localhost:11434 |
| LM Studio | http://localhost:1234/v1 |

---

## 五、推荐组合

- **日常中文文档**：PP-OCRv5（或 Tesseract）→ 双层 PDF
- **手写 / 复杂版面**：PaddleOCR-VL 或 DeepSeek-OCR
- **完全离线、零依赖**：Tesseract + RapidOCR(ONNX)
- **高质量但可接受联网**：Qwen-VL / GLM-4V / GPT-4o 视觉接口

> 隐私提醒：云端与大模型引擎会把图片上传到第三方，请勿用于身份证、合同等敏感文档。
