<#
ReqStudio installer for Windows (PowerShell)

Actions:
- Creates a virtualenv in the repo (.venv) and installs the project via pyproject.toml
- Creates Start Menu and Desktop shortcuts to launch the app with pythonw.exe

Usage:
  powershell -ExecutionPolicy Bypass -File install_reqstudio.ps1

Optional args:
  -VenvPath   <string>  # custom venv path (default: <repo>\.venv)
  -CreateDesktop        # also create a Desktop shortcut (default: on)
#>
[CmdletBinding()]
param(
  [string]$VenvPath,
  [switch]$CreateDesktop = $true
)

$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
  $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  return (Resolve-Path (Join-Path $scriptDir "..\.."))
}

function Resolve-Python {
  try {
    $py = & py -3 -c "import sys;print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $py) { return $py }
  } catch {}
  $pth = (Get-Command python -ErrorAction SilentlyContinue).Path
  if (-not $pth) { throw "Python 3 not found. Install Python 3.10+ and ensure it's on PATH or use the 'py' launcher." }
  return $pth
}

function Ensure-Version([string]$pythonExe) {
  $ver = & $pythonExe - << 'PY'
import sys
print("%d.%d" % sys.version_info[:2])
PY
  $maj,$min = $ver.Split('.')
  if ([int]$maj -lt 3 -or ([int]$maj -eq 3 -and [int]$min -lt 10)) {
    throw "Python $ver found; Python >= 3.10 required"
  }
}

function Install-PythonHeadless {
  Write-Host "[reqstudio] Python not found. Attempting headless installation..."
  $installed = $false

  # 1) Try winget
  if (-not $installed) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      try {
        Write-Host "[reqstudio] Installing via winget (Python.Python.3.11)..."
        winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        $installed = $true
      } catch {}
    }
  }

  # 2) Try Chocolatey
  if (-not $installed) {
    if (Get-Command choco -ErrorAction SilentlyContinue) {
      try {
        Write-Host "[reqstudio] Installing via Chocolatey (python)..."
        choco install -y python
        $installed = $true
      } catch {}
    }
  }

  # 3) Fallback: download official installer and run silent
  if (-not $installed) {
    try {
      $ver = '3.11.9'
      $arch = if ($env:PROCESSOR_ARCHITECTURE -match '64') { 'amd64' } else { 'win32' }
      $url = "https://www.python.org/ftp/python/$ver/python-$ver-$arch.exe"
      $tmp = Join-Path $env:TEMP "python-$ver-$arch.exe"
      Write-Host "[reqstudio] Downloading $url ..."
      try {
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
      } catch {
        # Fallback to BitsTransfer if IE engine restricted
        Start-BitsTransfer -Source $url -Destination $tmp
      }
      Write-Host "[reqstudio] Running silent installer..."
      & $tmp /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 SimpleInstall=1 Include_launcher=1
      $installed = $true
    } catch {
      Write-Warning "[reqstudio] Failed to download/install Python automatically: $_"
    }
  }

  if (-not $installed) {
    throw "Unable to install Python automatically. Please install Python 3.10+ and re-run."
  }
}

function Ensure-Git {
  if (Get-Command git -ErrorAction SilentlyContinue) { return }
  Write-Host "[reqstudio] Git not found. Attempting headless installation..."
  $installed = $false
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    try {
      Write-Host "[reqstudio] Installing Git via winget (Git.Git)..."
      winget install -e --id Git.Git --silent --accept-package-agreements --accept-source-agreements
      $installed = $true
    } catch {}
  }
  if (-not $installed -and (Get-Command choco -ErrorAction SilentlyContinue)) {
    try {
      Write-Host "[reqstudio] Installing Git via Chocolatey (git)..."
      choco install -y git
      $installed = $true
    } catch {}
  }
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warning "[reqstudio] Unable to install Git automatically. Please install Git for Windows and re-run."
  }
}

function New-Shortcut([string]$Path, [string]$Target, [string]$Args, [string]$WorkingDir, [string]$IconPath) {
  $WScriptShell = New-Object -ComObject WScript.Shell
  $shortcut = $WScriptShell.CreateShortcut($Path)
  $shortcut.TargetPath = $Target
  $shortcut.Arguments = $Args
  $shortcut.WorkingDirectory = $WorkingDir
  $shortcut.WindowStyle = 1
  if ($IconPath -and (Test-Path $IconPath)) { $shortcut.IconLocation = $IconPath }
  $shortcut.Save()
}

$repoRoot = (Get-RepoRoot).Path
Write-Host "[reqstudio] Repo root: $repoRoot"

if (-not $VenvPath) { $VenvPath = Join-Path $repoRoot '.venv' }
Write-Host "[reqstudio] Using venv: $VenvPath"

$python = $null
try {
  $python = Resolve-Python
  Ensure-Version $python
} catch {
  Install-PythonHeadless
  $python = Resolve-Python
  Ensure-Version $python
}

Ensure-Git

if (-not (Test-Path $VenvPath)) {
  Write-Host "[reqstudio] Creating virtualenv..."
  & $python -m venv $VenvPath
}

$venvPy = Join-Path $VenvPath 'Scripts\\python.exe'
& $venvPy -m pip install --upgrade pip
Write-Host "[reqstudio] Installing project via pyproject.toml..."
& $venvPy -m pip install $repoRoot

# Create Start Menu shortcut
$startMenuDir = Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs'
$lnkPath = Join-Path $startMenuDir 'ReqStudio.lnk'
$pythonw = Join-Path $VenvPath 'Scripts\\pythonw.exe'
$icon = Join-Path $repoRoot 'media\\reqstudio_logo.ico'
New-Shortcut -Path $lnkPath -Target $pythonw -Args 'app.py' -WorkingDir $repoRoot -IconPath $icon
Write-Host "[reqstudio] Start Menu shortcut created: $lnkPath"

if ($CreateDesktop) {
  $deskLnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'ReqStudio.lnk'
  New-Shortcut -Path $deskLnk -Target $pythonw -Args 'app.py' -WorkingDir $repoRoot -IconPath $icon
  Write-Host "[reqstudio] Desktop shortcut created: $deskLnk"
}

Write-Host "[reqstudio] Done. Launch ReqStudio from Start Menu or Desktop."
