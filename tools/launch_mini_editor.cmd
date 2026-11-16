@echo off
setlocal
pushd "%~dp0.."
python "%~dp0launch_mini_editor.py" --execute --bundle "%~dp0..\build\hyperrig-mini-qualified-editor"
if errorlevel 1 pause
popd
endlocal
