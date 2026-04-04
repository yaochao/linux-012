@echo off
setlocal
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-window.ps1" %*
exit /b %ERRORLEVEL%
