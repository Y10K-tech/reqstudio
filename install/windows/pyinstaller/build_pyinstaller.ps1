$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = (Resolve-Path (Join-Path $here '..\..\..')).Path

Set-Location $root

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  Write-Host "Installing PyInstaller..."
  python -m pip install pyinstaller
}

$icon = Join-Path $root 'media\reqstudio_logo.ico'
$addData = @(
  # Include core package and media folder if needed at runtime
  "core;core",
  "media;media"
)

$addDataArgs = @()
foreach ($d in $addData) { $addDataArgs += @('--add-data', $d) }

pyinstaller `
  --noconsole `
  --name ReqStudio `
  --icon "$icon" `
  @addDataArgs `
  app.py

Write-Host "Build complete: dist\ReqStudio\ReqStudio.exe"
