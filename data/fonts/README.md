# 字体 (data/fonts)

吏部在生成双层 PDF / Word 时会为中文字符嵌入字体。默认优先使用系统已安装的中文字体
（Noto Sans CJK、思源黑体、文泉驿等），PyMuPDF 内置的 `china-s` CJK 字体作为兜底，
因此**开箱即用、无需手动安装字体**。

如果希望获得更统一的外观，可将 `.ttf` / `.otf` 字体放入本目录，软件会在启动时自动加载。
推荐字体（均为开源许可）：

- HarmonyOS Sans SC：https://developer.harmonyos.com/cn/design/resource
- 思源黑体 (Source Han Sans)：https://github.com/adobe-fonts/source-han-sans
- 霞鹜文楷 (LXGW WenKai)：https://github.com/lxgw/LxgwWenKai

> 本仓库不预置任何字体文件，以避免许可证与体积问题。
