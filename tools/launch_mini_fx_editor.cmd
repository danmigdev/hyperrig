@echo off
setlocal
pushd "%~dp0.."
python "%~dp0launch_mini_fx_editor.py" --execute --bundle "%~dp0..\build\hyperrig-mini-fx-editor"
if errorlevel 1 pause
popd
endlocal
