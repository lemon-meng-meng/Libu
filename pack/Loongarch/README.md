# 吏部 · LoongArch 打包说明

本目录用于在 **LoongArch（龙芯）** 平台上生成 `.deb` 与 `.AppImage`。

## 一键打包脚本

| 脚本 | 作用 | 产物 |
| --- | --- | --- |
| `build.sh` | 一次生成 Deb + AppImage（推荐） | 见下 |
| `build-deb.sh` | 仅生成 Deb | `../releases/libu_<版本>_loongarch64.deb` |
| `build-appimage.sh` | 仅生成 AppImage | `../releases/libu-loongarch64.AppImage` |

```bash
bash build.sh                 # 一键全部
bash build-deb.sh             # 只打 Deb
bash build-appimage.sh        # 只打 AppImage
```

产物输出到仓库根目录 `releases/`：

- `libu_<版本>_loongarch64.deb`
- `libu-loongarch64.AppImage`

> 0.3.0 起吏部使用系统 WebKitGTK 原生窗口运行，Deb 依赖
> `python3-gi`、`gir1.2-gtk-3.0`、`gir1.2-webkit2-4.1`。
>
> 0.4.0 起截屏 OCR 的全局快捷键在 Linux 原生窗口路径下需要 `python3-xlib`
> 或 `gir1.2-keybinder-3.0`（已列入 Deb 的 Recommends；Wayland 下建议改用托盘菜单）。

## 环境要求

- 龙芯原生系统：Loongnix、龙芯 Debian 或已配置 loongarch64 chroot
- `python3`、`python3-venv`、`dpkg-deb`
- 可选：`npm`（构建前端；若已存在 `src/frontend/dist` 可省略）
- AppImage 需要 `libfuse2`（运行 AppImage 时）

跨架构构建时脚本会拒绝执行，可设置 `LIBU_FORCE=1` 仅做结构生成。

## OCR 引擎在 LoongArch 上的建议

| 引擎 | 可用性 | 说明 |
| --- | --- | --- |
| Tesseract | ✅ 推荐 | `apt install tesseract-ocr tesseract-ocr-chi-sim` |
| 自定义 ONNX（RapidOCR） | ✅ 推荐 | `pip install rapidocr-onnxruntime onnxruntime`，导入 `OCR Model/paddleocr_ppocrv5.zip` 即可 |
| 微信 OCR | ⚠ 见下 | `.xnet` 权重跨平台通用，但需微信客户端运行库；且微信官方暂未提供 loongarch 运行库，通常不可用 |
| PaddleOCR | ⚠ 视情况 | 需龙芯版 PaddlePaddle，可从源码编译 |
| 在线 / 大模型 API | ✅ | 与架构无关，联网即可 |

## 备注

微信 OCR 的模型文件（`.xnet`）本身与平台无关，Windows 与 Linux 通用；
但其推理运行库（`libwxocr.so` / `wxocr`）按平台编译。LoongArch 上一般无法直接使用，
建议优先使用 Tesseract 或自定义 ONNX 模型。
