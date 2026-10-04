@echo off
REM SPDX-License-Identifier: GPL-3.0-or-later
REM 吏部 Windows 一键打包入口
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0package_windows.ps1" %*
if errorlevel 1 (
  echo 打包失败。
  exit /b 1
)
echo 打包完成。
endlocal
