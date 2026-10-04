# 吏部 · Windows 打包

## 一键打包

双击 `build.bat`，或在 PowerShell 中执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\package_windows.ps1
```

可选参数：

```powershell
# 同时用 PyInstaller 打包内置后端 exe（双击即用，无需另装 Python）
.\package_windows.ps1 -WithBackend

# 跳过前端构建（已存在 src\frontend\dist 时）
.\package_windows.ps1 -SkipFrontend
```

## 前置依赖

- Python 3.10+
- Node.js 18+
- 首次构建会创建 `.venv-win` 并安装 `requirements.txt`

## 产物

- `releases\windows\`：NSIS 安装包与便携版（exe）
- 若使用 `-WithBackend`：`src\frontend\backend\libu-backend.exe`（随安装包内置）

## 说明

 - Electron 主进程会自动查找内置后端 `resources\backend\libu-backend.exe`；
  找不到时回退到系统 Python 运行 `python -m libu serve`。
- 0.4.0 起支持在设置中自定义截屏快捷键（默认 `Ctrl+Alt+O`）；Electron 已显式
  授权屏幕捕获，点击托盘「截屏 OCR」或按快捷键即可在屏幕框选识别。
- 0.4.0 起支持**批量扫描**：一次导入多张图片合成多页 PDF / Word，可调整页面顺序。
- OCR 引擎：Windows 上推荐 Tesseract（安装时勾选中文包）、RapidOCR(ONNX) 或在线/大模型接口。
  也可导入随附的 `OCR Model/paddleocr_ppocrv5.zip`（PP-OCRv5 ONNX）。
- 微信 OCR：需 Windows 版微信的对应运行库，`.xnet` 权重跨平台通用。
- 模型自动检测：Ollama / LM Studio 可在设置中一键拉取模型列表并保存多个模型。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `build.bat` | 双击即用的一键打包入口 |
| `package_windows.ps1` | 实际打包脚本（前端 + 可选 PyInstaller 后端 + electron-builder） |
| `libu-backend.spec` | PyInstaller 配置，生成独立后端 exe |
| `launcher.py` | 后端绝对导入入口（避免冻结后相对导入失效） |
