#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部 · LoongArch Deb 一键打包脚本
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
exec bash packaging/build-deb.sh loongarch64
