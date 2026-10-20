@echo off
title ApexClicker Pro
echo Starting ApexClicker Pro...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with an error.
    pause
)
