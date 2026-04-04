@echo off
setlocal
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify-userland.ps1" %*
exit /b %ERRORLEVEL%
