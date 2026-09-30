# Cognitive AI — PowerShell Launcher
$Host.UI.RawUI.WindowTitle = "Cognitive AI — Fatigue & Wellbeing OS"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   ⚡ Launching Cognitive AI Desktop Operating System   " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot

python run.py $args

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[Error] Application exited with code $LASTEXITCODE" -ForegroundColor Red
    Read-Host -Prompt "Press Enter to exit..."
}
