$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @('py', '-3')
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @('python')
    }
    throw 'Python 3 not found. Install Python 3 and ensure py or python is on PATH.'
}

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $Root

$PythonCommand = Get-PythonCommand
$PythonExe = $PythonCommand[0]
$PythonArgs = @()
if ($PythonCommand.Length -gt 1) {
    $PythonArgs = $PythonCommand[1..($PythonCommand.Length - 1)]
}

& $PythonExe @PythonArgs (Join-Path $Root 'rebuild/driver.py') 'verify' @args
exit $LASTEXITCODE
