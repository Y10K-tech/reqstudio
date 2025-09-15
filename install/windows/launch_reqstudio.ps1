<#
Launch ReqStudio from an installed directory.
Finds the local .venv and uses pythonw.exe to run app.py without a console window.
#>
$ErrorActionPreference = 'Stop'

function Get-Here { Split-Path -Parent $MyInvocation.MyCommand.Path }
$root = (Resolve-Path (Join-Path (Get-Here) '..\..')).Path
$venv = Join-Path $root '.venv'
$pythonw = Join-Path $venv 'Scripts\pythonw.exe'
if (-not (Test-Path $pythonw)) {
  throw "pythonw.exe not found at $pythonw. Run install_reqstudio.ps1 to set up the virtualenv."
}

Start-Process -FilePath $pythonw -ArgumentList 'app.py' -WorkingDirectory $root
