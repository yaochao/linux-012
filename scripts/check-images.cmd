@echo off
setlocal
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0check-images.ps1" %*
exit /b %ERRORLEVEL%
