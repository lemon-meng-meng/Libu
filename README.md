# 吏部 · Libu

> 图片 / 扫描件 → 可搜索的电子版 PDF / Word  
> 核心是**图片转电子文档**，OCR 只是达成这一目标的重要手段。

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](LICENSE)

## 简介

吏部把手机拍摄或扫描的纸张图片，处理成"接近原生电子版"的文档：

- **双层 PDF**：原图外观 + 不可见文字层，可搜索、可复制、可选中（像 OCRmyPDF 的效果）。
- **Word（原图可复制）**：保留原图，叠加可复制的隐形文字。
- **Word（纯文本）**：按阅读顺序重排文字，去除图片等多余元素。
- **图像增强**：透视/倾斜矫正、去阴影、白底化，尽量还原"电子版"观感。

处理结果默认保存到 **`~/文档/吏部`**。

## 功能特性

- 导入图片后**拖拽框选**纸面范围，随后弹出「是否 OCR」选项。
- **批量扫描**：一次导入多张图片，合成为多页双层 PDF / Word；编辑界面可拖拽调整页面顺序。
- 不启用 OCR 时，直接做图像增强并输出 PDF。
- OCR 后进入**文字校正**界面：逐行修改、删除，原图框高亮对照，确认后再输出。
- **多 OCR 引擎**（共 28 个），分为四类：
  - **本地模型**：Tesseract、PaddleOCR、PP-OCRv5、PaddleOCR-VL、自定义 ONNX（RapidOCR）、微信 OCR、ModernVBERT、MonkeyOCR、DeepSeek-OCR
  - **在线 OCR 引擎**：OCR.space、百度云 OCR、PaddleOCR 在线（飞桨星河）（会有隐私提示）
  - **大模型 API**：DeepSeek、GLM、Kimi、MiniMax、阶跃星辰、Qwen、零一万物、英伟达、腾讯混元
  - **Agent / 本地 AI 助手**：OpenCode、DeepSeek Harness、Claude Code、Codex、Cherry Studio、Ollama、LM Studio
- **微信 OCR**：一键导入 `wechat_ocr.zip` 即可使用（详见下文说明）。
- **PaddleOCR 离线**：随附 `OCR Model/paddleocr_ppocrv5.zip`（PP-OCRv5 ONNX），
  导入后配合「自定义本地模型 (ONNX)」即可离线识别。
- **模型自动检测**：Ollama / LM Studio / OpenAI 兼容服务可自动拉取模型列表，
  保存多个模型并切换使用。
- **OCR 图片查看器**：像微信一样在图片上直接框选复制文字；支持应用内导入、
  `Ctrl+V` 粘贴、从文件管理器直接打开；记忆打开过的图片（文件未移动/删除即保留），
  兼容 `.jpg/.jpeg/.jfif/.png/.bmp/.tif/.tiff/.webp/.gif/.ico/.tga/.avif/.heic/.heif/.jp2` 等广泛格式。
- **截屏 OCR**：托盘点击「截屏 OCR」后在屏幕框选，识别结果进入可自由编辑的剪贴板，
  一键「复制文字」；另提供应用内框选作为备选。
- **按功能选择模型**：文档扫描仪、图片查看器、截屏 OCR 可分别使用不同的 OCR 供应商，互不影响。
- **液态玻璃 UI**：遵循 [liquid-glass-react](https://github.com/rdev/liquid-glass-react) 设计语言。
- **主题与底色**：暗色 / 亮色 / 跟随系统，内置 8 种渐变底色可切换。
- **最近项目**：块状 / 条状两种显示；右键可「不在软件内显示该文件」或「删除文件」；「+」按钮与文件等大。
- **独立运行**：使用系统 WebKitGTK 原生窗口，无需浏览器即可作为独立软件运行。
- **文件管理器集成**：右键图片可直接「用吏部打开」（Nautilus 扩展 + 脚本兜底）。

## 界面

左侧工具栏四个按钮（自上而下）：显示「主」字的主界面、「图」字的图片查看器、
「截」字的截屏 OCR、齿轮图标的设置界面。  
每个文件底座、按钮、模型提供商设置模块都是一块独立的"液态玻璃"。

## 安装与运行

### 方式一：从源码运行

```bash
# 1. 安装后端依赖
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. 构建前端（可选；不构建则用 Electron 开发模式）
cd src/frontend && npm install && npm run build && cd ../..

# 3. 启动
PYTHONPATH=src python3 -m libu serve
# 浏览器打开 http://127.0.0.1:8000
```

在 Linux 桌面可直接运行启动器：

```bash
bash bin/libu          # 启动服务并打开浏览器
```

### 方式二：Electron 桌面开发

```bash
# 终端 1：后端
PYTHONPATH=src python3 -m libu serve

# 终端 2：前端
cd src/frontend
npm install
npm run dev            # Vite 开发服务器
npm run electron       # 打开 Electron 窗口
```

### 方式三：安装打包产物

```bash
# Debian / Ubuntu
sudo apt install ./releases/libu_0.3.0_amd64.deb
libu-app

# AppImage
chmod +x releases/libu-x86_64.AppImage
./releases/libu-x86_64.AppImage
```

### 方式四：用户级一键安装脚本（无需 root）

```bash
bash install.sh                 # 安装到 ~/.local/share/libu
bash scripts/install-context-menu.sh   # 安装文件管理器右键菜单（可选）
```

## 打包

| 平台 | 一键脚本 | 说明 |
| --- | --- | --- |
| Debian / Ubuntu | `bash packaging/build-deb.sh [架构]` | 生成 `.deb`，内置虚拟环境 |
| AppImage | `bash packaging/build-appimage.sh [架构]` | 生成 `.AppImage` |
| Windows | `pack/Windows/build.bat` | 生成 NSIS 安装包 / 便携版 |
| LoongArch | `bash pack/Loongarch/build.sh` | 生成龙芯 deb 与 AppImage |

可选环境变量：`LIBU_INCLUDE_WECHAT=1` 将 `wechat_ocr.zip` 一并打入安装包。

## 微信 OCR 说明

`OCR Model/wechat_ocr.zip` 内含：

```
wechat_ocr_pkg/
├── wxocr                 # 启动器（按平台编译）
├── libwxocr.so           # Linux x86_64 运行库
└── ocr_model/            # .xnet 权重 + 字符集（跨平台通用）
```

- **模型（`.xnet`）本身与平台无关**，Windows 与 Linux 通用；
- **运行库（`wxocr` / `libwxocr.so`）按平台编译**，且依赖微信客户端的 `libmmmojo.so` 等库；
- 在软件「设置 → 本地 OCR 模型」中导入该 zip 即可；若运行时缺少微信库，可在设置中指定运行库目录或自定义命令模板。
- 由于运行库为腾讯专有组件，本项目不分发，需用户自备（通常来自本机安装的微信客户端）。

## 目录结构

```
吏部/
├── src/libu/                # Python 后端
│   ├── api.py               # FastAPI 服务
│   ├── service.py           # 业务编排
│   ├── viewer.py            # OCR 图片查看器（记忆/粘贴/识别）
│   ├── screenshot.py        # 截屏 OCR 剪贴板状态
│   ├── tray_helper.py       # GTK 托盘 + 区域截屏助手
│   ├── pdf_word_generator.py# 双层 PDF / Word 生成
│   ├── image_processing.py  # 图像增强
│   ├── settings.py          # 设置持久化
│   ├── model_manager.py     # 本地模型管理
│   ├── vision_client.py     # 大模型视觉接口
│   └── ocr_backends/        # 28 个 OCR 引擎
├── src/frontend/            # Electron + React 前端
│   ├── electron/            # 主进程
│   └── src/components/      # 液态玻璃 UI 组件
├── packaging/               # deb / AppImage 脚本
├── pack/Windows/            # Windows 打包
├── pack/Loongarch/          # 龙芯打包
├── OCR Model/               # 微信 OCR 模型与下载文档
├── data/icons/              # 图标
├── data/fonts/              # 可选字体目录
├── data/libu.metainfo.xml   # AppStream 元数据
├── nautilus-extension/      # 文件管理器右键菜单扩展
├── locale/                  # 多语言（gettext）
├── tests/                   # 单元测试
├── bin/                     # 启动器
├── debian/                  # Debian 打包目录
├── install.sh               # 用户级一键安装
└── releases/                # 构建产物
```

## 测试

```bash
python -m unittest discover -s tests -v
```

## 隐私与安全

- 所有配置与 API Key 仅存放于本机 `~/.config/libu/settings.json`，不会上传。
- **本地引擎**：数据不出本机。
- **在线 / 大模型 / Agent 引擎**：图片会上传到对应服务，界面中会显式提示风险，请勿用于敏感文档。

## 许可证

[GPL-3.0-or-later](LICENSE)。第三方组件声明见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。

Copyright (c) 2026 lemon-meng-meng。

> 本项目与汉王科技、腾讯微信等公司无任何关联。
