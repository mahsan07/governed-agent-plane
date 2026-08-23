$ErrorActionPreference = "Stop"
python (Join-Path $PSScriptRoot "demo.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
