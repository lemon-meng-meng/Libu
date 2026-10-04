# SPDX-License-Identifier: GPL-3.0-or-later
# 吏部 Windows 一键打包脚本
# 生成：NSIS 安装包 + 便携版 + 可选内置后端 exe
param(
  [string]$Version = "0.4.0",
  [switch]$WithBackend,
  [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root
Write-Host "==> 吏部 Windows 打包 v$Version" -ForegroundColor Cyan

function Require($name, $cmd) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    throw "缺少 $name（$cmd），请先安装后重试。"
  }
}
Require "Python 3" "python"
Require "Node.js" "node"

# 1) 前端
if (-not $SkipFrontend) {
  Write-Host "==> 构建前端" -ForegroundColor Cyan
  Push-Location "src\frontend"
  npm install --no-audit --no-fund
  npm run build
  Pop-Location
}

# 2) 后端虚拟环境
Write-Host "==> 准备后端虚拟环境" -ForegroundColor Cyan
if (-not (Test-Path ".venv-win")) {
  python -m venv .venv-win
}
& ".venv-win\Scripts\python.exe" -m pip install --upgrade pip
& ".venv-win\Scripts\python.exe" -m pip install -r requirements.txt

if ($WithBackend) {
  Write-Host "==> 使用 PyInstaller 打包后端" -ForegroundColor Cyan
  & ".venv-win\Scripts\python.exe" -m pip install pyinstaller
  & ".venv-win\Scripts\pyinstaller.exe" --noconfirm --clean "pack\Windows\libu-backend.spec"
  New-Item -ItemType Directory -Force -Path "src\frontend\backend" | Out-Null
  Copy-Item "dist\libu-backend\*" "src\frontend\backend\" -Recurse -Force
}

# 3) Electron 安装包
Write-Host "==> 使用 electron-builder 生成安装包" -ForegroundColor Cyan
Push-Location "src\frontend"
npm install --no-audit --no-fund
npx electron-builder --win --config.extraMetadata.version=$Version
Pop-Location

New-Item -ItemType Directory -Force -Path "releases\windows" | Out-Null
Get-ChildItem "releases\electron" -Include *.exe,*.nsis,*portable* -Recurse -ErrorAction SilentlyContinue |
  Copy-Item -Destination "releases\windows\" -Force

Write-Host "完成：releases\windows" -ForegroundColor Green
