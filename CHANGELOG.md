# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.4.0] - 2026-10-04

### Added
- **批量扫描**：一次导入多张图片，逐页框选后合成为**多页双层 PDF / Word**；
  编辑界面可拖拽调整页面顺序，支持「上移 / 下移 / 移除 / 追加图片」。
- **提供商模型自动检测**：Ollama、LM Studio 及所有 OpenAI 兼容服务支持
  「自动检测模型 / 测试连接」，可勾选保存**多个模型**并指定当前使用的模型；
  连接失败时给出可读的具体原因（端口、服务是否启动等）。
- **PaddleOCR 在线**：在线 OCR 引擎新增「PaddleOCR 在线（飞桨星河）」
  （https://aistudio.baidu.com/paddleocr）。
- **PP-OCRv5 ONNX 一键导入包**：随附 `OCR Model/paddleocr_ppocrv5.zip`
  （mobile det/rec/cls + 字典），导入后配合「自定义本地模型 (ONNX)」即可离线识别；
  提供 `scripts/build-paddleocr-model.sh` 重建。

### Fixed
- **液态玻璃文字可读性**：为右键菜单等液态玻璃上的文字添加**渐变描边**
  （左上最浅、右下最深，颜色取自当前底色，切换底色时同步变化）。
- **截屏 OCR 快捷键**：Electron 外壳显式授权 `getDisplayMedia` 屏幕捕获，
  并读取设置中的自定义快捷键；Linux 原生窗口路径新增 GTK 全局快捷键支持
  （keybinder / X11 Xlib）。
- 修复 API Key 首尾空白导致的 401 鉴权失败。

## [0.3.0] - 2026-10-03

### Added
- **OCR 图片查看器**：类微信的图片文字复制体验。图片上直接框选即可复制文字；
  支持从文件管理器直接打开、应用内导入、`Ctrl+V` 粘贴图片，并记忆打开过的图片
  （文件未移动/删除即一直保留）。兼容更广的图片格式。
- **截屏 OCR**：系统托盘点击「截屏 OCR」后在屏幕框选，识别结果进入可自由编辑的
  剪贴板，并提供「复制文字」按钮；另提供应用内框选作为备选。
- **按功能选择模型**：文档扫描仪、图片查看器、截屏 OCR 可分别指定不同的 OCR
  供应商，互不影响；每个界面均有「选择模型」按钮。
- **渐变底色**：在内置蓝底基础上新增 7 种渐变底色（午夜紫、落日玫瑰、翡翠夜、
  石墨灰、黎明、深海、森林），可在设置中切换。
- 侧栏新增「图片查看器（图）」「截屏 OCR（截）」入口，顺序为
  主界面 / 图片查看器 / 截屏 OCR / 设置。
- 使用系统 WebKitGTK 的原生窗口启动器（`bin/libu-window`），无需浏览器即可
  作为独立软件运行；Electron 外壳新增托盘与全局快捷键。

### Fixed
- 修复设置界面液态玻璃裁切内容、遮挡文字/按钮的问题（`overflow` 与高光层调整）。
- 修复打包后前端 API 指向固定 `:8000`、与实际服务端口不一致导致界面无法加载数据的问题。
- 修复提供商卡片展开时内容显示不完整的问题。

## [0.2.1] - 2026-10-03

### Fixed
- 修复 OCR 校正后选择输出格式无效、生成结果为空的问题（输出键与路径映射混淆）。
- 修复 Agent / 本地 AI 助手在大模型设置中无法启用的问题（补充 `enabled` 开关）。
- 修复液态玻璃内容包裹层破坏文件卡片块状 / 条状布局的问题。
- 修复图片框选默认范围被错误上报为 `[0,0,0,0]` 的问题。
- 修复 OCR 校正界面文字高亮框缩放比例错误（改用原图宽度换算）。
- 修复导入多张图片时只处理第一张的问题。
- 修复「打开所在位置」实际打开文件而非所在目录的问题（新增 reveal IPC）。
- 修复隐藏项目仍会显示、以及乐观更新可能覆盖其它提供商配置的问题。
- 修复微信 OCR 自定义命令模板在设置界面无法填写的问题。
- 修复 Windows PyInstaller 入口相对导入失效、后端资源未随包分发的问题。

### Added
- 右键菜单 / 项目详情支持在文件管理器中定位文件。
- 本地化（locale）目录、Nautilus 右键菜单扩展、`install.sh` 一键安装脚本。
- `data/libu.metainfo.xml`、`debian/copyright` 等发行元数据。

## [0.2.0] - 2026-10-02

### Added
- 双层 PDF 生成：原图 + 不可见 OCR 文字层，可搜索、可复制、可选中。
- Word 两种输出：原图 + 可复制隐形文字；保留阅读顺序的纯文本 Word。
- 拖拽框选纸面范围，导入时弹出「是否 OCR」选项。
- OCR 文字校正界面：逐行编辑，原图框高亮对照。
- 多引擎框架（27 个引擎）：
  - 本地：Tesseract、PaddleOCR、PP-OCRv5、PaddleOCR-VL、自定义 ONNX(RapidOCR)、微信 OCR、ModernVBERT、MonkeyOCR、DeepSeek-OCR
  - 在线：OCR.space、百度云 OCR
  - 大模型：DeepSeek、GLM、Kimi、MiniMax、阶跃星辰、Qwen、零一万物、英伟达、混元
  - Agent：OpenCode、DeepSeek Harness、Claude Code、Codex、Cherry Studio、Ollama、LM Studio
- 微信 OCR 模型导入（`wechat_ocr.zip`）。
- 液态玻璃 UI、暗色 / 亮色 / 跟随系统主题。
- 最近项目块状 / 条状显示、右键「不在软件内显示」与「删除文件」。
- 图像预处理：纠偏、去阴影、白底增强。
- 输出目录 `~/文档/吏部`。
- 打包：Deb、AppImage、Windows(NSIS)、LoongArch。

## [0.1.0] - 2026-10-01

### Added
- 项目骨架与初始目录结构。
- 微信 OCR 模型提取脚本与下载地址文档。
- 初版 PDF/Word 生成模块与前端骨架。

[0.2.1]: https://github.com/lemon-meng-meng/Libu/releases/tag/v0.2.1
[0.2.0]: https://github.com/lemon-meng-meng/Libu/releases/tag/v0.2.0
[0.1.0]: https://github.com/lemon-meng-meng/Libu/releases/tag/v0.1.0
