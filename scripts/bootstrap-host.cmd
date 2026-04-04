@echo off
setlocal
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap-host.ps1" %*
exit /b %ERRORLEVEL%
