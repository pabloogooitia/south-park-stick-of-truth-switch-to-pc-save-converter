@echo off
rem Drag a JKSV/Checkpoint backup folder or zip onto this file (needs Python 3.8+).
cd /d "%~dp0.."
py -3 -m sot_save_converter %*
if errorlevel 9009 python -m sot_save_converter %*
pause
