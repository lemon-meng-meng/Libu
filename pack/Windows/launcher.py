# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部后端独立可执行文件入口（供 PyInstaller 使用）。
# 通过绝对包名导入，避免冻结后相对导入失效。
import sys

from libu.cli import main

if __name__ == "__main__":
    sys.exit(main())
