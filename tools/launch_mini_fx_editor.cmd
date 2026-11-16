@echo off
setlocal
pushd "%~dp0.."
python "%~dp0launch_hyperrig_editor.py" --execute --bundle "%~dp0..\build\hyperrig-mini-english-editor"
if errorlevel 1 pause
popd
endlocal
