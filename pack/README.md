# 吏部 · 跨平台打包

本目录集中存放 **Windows** 与 **LoongArch（龙芯）** 的一键打包脚本与所需文件。
Linux x86_64 的 Deb / AppImage 由仓库根目录 `packaging/` 下的脚本生成。

| 目标产物 | 平台 | 一键脚本 |
| --- | --- | --- |
| Windows `.exe`（NSIS 安装包 / 便携版） | Windows 10+ | `pack/Windows/build.bat` |
| LoongArch `.deb` | LoongArch（龙芯） | `pack/Loongarch/build-deb.sh` |
| LoongArch `.AppImage` | LoongArch（龙芯） | `pack/Loongarch/build-appimage.sh` |
| LoongArch（两者一起） | LoongArch（龙芯） | `pack/Loongarch/build.sh` |
| Linux x86_64 `.deb` / `.AppImage` | Debian / Ubuntu | `packaging/build-deb.sh`、`packaging/build-appimage.sh` |

## Windows（exe）

```bat
:: 双击，或在命令行执行
pack\Windows\build.bat

:: 可选：内置独立后端 exe（目标机器无需安装 Python）
powershell -ExecutionPolicy Bypass -File pack\Windows\package_windows.ps1 -WithBackend
```

产物输出到 `releases\windows\`（NSIS 安装包 + 便携版）。
详见 [`Windows/README.md`](Windows/README.md)。

## LoongArch（Deb / AppImage）

在龙芯原生系统（Loongnix / 龙芯 Debian）中执行：

```bash
bash pack/Loongarch/build.sh          # 同时生成 deb 与 AppImage
bash pack/Loongarch/build-deb.sh      # 仅 Deb
bash pack/Loongarch/build-appimage.sh # 仅 AppImage
```

产物输出到仓库根目录 `releases/`。详见 [`Loongarch/README.md`](Loongarch/README.md)。

## 关于 OCR 模型

- `OCR Model/paddleocr_ppocrv5.zip`：PP-OCRv5 ONNX 一键导入包，随 Deb / AppImage 一并分发。
- `OCR Model/wechat_ocr.zip`：微信 OCR 运行时（需自备运行库），可用
  `LIBU_INCLUDE_WECHAT=1` 打入安装包。
- 生成的安装包均可在软件「设置 → 本地 OCR 模型 → 导入模型 zip」中导入上述压缩包。
