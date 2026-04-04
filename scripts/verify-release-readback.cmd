@echo off
setlocal
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify-release-readback.ps1" %*
exit /b %ERRORLEVEL%
