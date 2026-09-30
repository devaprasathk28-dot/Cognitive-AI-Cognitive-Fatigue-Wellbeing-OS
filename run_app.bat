@echo off
title Cognitive AI — Fatigue & Wellbeing OS
cd /d "%~dp0"

echo ========================================================
echo   Launching Cognitive AI Desktop Operating System
echo ========================================================

python run.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while launching Cognitive AI.
    pause
)
