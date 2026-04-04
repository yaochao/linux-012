@echo off
setlocal
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0fetch-release-images.ps1" %*
exit /b %ERRORLEVEL%
