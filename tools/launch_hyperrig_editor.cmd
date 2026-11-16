@echo off
setlocal
pushd "%~dp0.."
python "%~dp0launch_mini_installer.py" --editor --bundle "%~dp0..\build\hyperrig-mini-installer-one-switch-preview-05"
if errorlevel 1 pause
popd
endlocal
