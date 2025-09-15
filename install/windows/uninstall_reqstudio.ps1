<#
ReqStudio uninstaller for Windows (PowerShell)

Removes:
- Start Menu and Desktop shortcuts
- Optional: the created virtualenv (default: remove)
#>
[CmdletBinding()]
param(
  [string]$VenvPath,
  [switch]$KeepVenv = $false
)

$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
  $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  return (Resolve-Path (Join-Path $scriptDir "..\.."))
}

$repoRoot = (Get-RepoRoot).Path
if (-not $VenvPath) { $VenvPath = Join-Path $repoRoot '.venv' }

# Remove shortcuts
$startMenuDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$lnkPath = Join-Path $startMenuDir 'ReqStudio.lnk'
if (Test-Path $lnkPath) { Remove-Item $lnkPath -Force }

$deskLnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'ReqStudio.lnk'
if (Test-Path $deskLnk) { Remove-Item $deskLnk -Force }

Write-Host "[reqstudio] Removed shortcuts."

if (-not $KeepVenv -and (Test-Path $VenvPath)) {
  Remove-Item $VenvPath -Recurse -Force
  Write-Host "[reqstudio] Removed virtualenv: $VenvPath"
} else {
  Write-Host "[reqstudio] Kept virtualenv: $VenvPath"
}

Write-Host "[reqstudio] Uninstall complete."
