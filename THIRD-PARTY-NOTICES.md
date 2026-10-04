# 第三方组件与许可证声明 · THIRD-PARTY NOTICES

本项目（吏部 · Libu）以 **GPL-3.0-or-later** 发布。下列第三方组件分别遵循其自身许可证，
本项目仅通过依赖调用或 API 方式使用，未修改其源代码（除非另有说明）。

## 运行依赖

| 组件 | 许可证 | 用途 |
| --- | --- | --- |
| FastAPI | MIT | 本地 HTTP 服务 |
| Uvicorn | BSD-3-Clause | ASGI 服务器 |
| Starlette | BSD-3-Clause | Web 框架 |
| Pydantic | MIT | 数据校验 |
| PyMuPDF (MuPDF) | AGPL-3.0 / 商业双许可 | 生成双层 PDF |
| python-docx | MIT | 生成 Word |
| Pillow | HPND / PIL License | 图像处理 |
| Requests | Apache-2.0 | HTTP 客户端 |
| NumPy | BSD-3-Clause | 数值计算 |
| OpenCV (可选) | Apache-2.0 | 图像增强 |
| python-multipart | Apache-2.0 | 文件上传解析 |

## 前端

| 组件 | 许可证 | 用途 |
| --- | --- | --- |
| React | MIT | UI 框架 |
| React DOM | MIT | DOM 渲染 |
| Vite | MIT | 构建工具 |
| Electron | MIT | 桌面外壳 |
| electron-builder | MIT | 桌面打包 |

> 界面遵循 [liquid-glass-react](https://github.com/rdev/liquid-glass-react) 的设计语言，
> 本项目以自研 CSS 组件 `LiquidGlass` 实现同等视觉效果，未复制其源代码。

## OCR 引擎（可选，由用户自行安装或配置）

| 引擎 | 许可证 | 说明 |
| --- | --- | --- |
| Tesseract OCR | Apache-2.0 | 通过 pytesseract 调用系统引擎 |
| PaddleOCR / PP-OCRv5 / PaddleOCR-VL | Apache-2.0 | 通过 `paddleocr` Python 包调用 |
| RapidOCR / ONNX Runtime | Apache-2.0 / MIT | 自定义 ONNX 本地模型 |
| OCR.space | 服务条款 | 在线 API，需用户自行申请 Key |
| 百度云 OCR | 服务条款 | 在线 API，需用户自行申请 Key |
| DeepSeek / GLM / Kimi / MiniMax / 阶跃 / Qwen / 零一万物 / NVIDIA | 各自服务条款 | 大模型视觉接口 |
| 微信 OCR | 微信客户端许可 | 模型权重来自用户本机微信客户端，本项目不分发 |

## 字体

界面默认使用系统字体（Noto Sans CJK / 思源黑体 / HarmonyOS Sans / 苹方 / 微软雅黑），
不随本项目分发任何字体文件。

## 免责声明

- 本项目与 **汉王科技**、**腾讯微信**、**百度**、**OpenAI** 等公司无任何关联。
- 使用在线 OCR / 大模型引擎时，图片会上传至相应第三方服务器，请自行评估隐私风险。
- 微信 OCR 模型的知识产权归腾讯所有，本项目仅提供导入本地模型的工具能力。

## 商标

「吏部 · Libu」名称与图标不在代码许可证授权范围内，商业产品不得使用本项目名称与图标进行宣传。
