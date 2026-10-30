@echo off
echo Stopping all services ...
taskkill /F /IM node.exe /T 2>nul
taskkill /F /IM python.exe /T 2>nul
echo Done.
pause
