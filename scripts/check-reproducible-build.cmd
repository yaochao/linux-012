@echo off
setlocal
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0check-reproducible-build.ps1" %*
exit /b %ERRORLEVEL%
