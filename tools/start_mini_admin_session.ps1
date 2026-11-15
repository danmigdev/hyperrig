param(
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^analysis/hardware/mini-admin-[0-9a-f]{32}$')]
    [string]$Session,
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^[0-9a-f]{64}$')]
    [string]$SessionSHA
)
$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$manifest = Join-Path $workspace ($Session + '/session.json')
if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant() -cne $SessionSHA) {
    throw 'Session manifest hash changed'
}
$config = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
$python = 'C:\Python312\python.exe'
if ($config.python_path -ine $python -or
    (Get-FileHash -LiteralPath $python -Algorithm SHA256).Hash.ToLowerInvariant() -cne $config.python_sha256) {
    throw 'Pinned Python executable differs'
}
foreach ($name in @('tools/mini_admin_session.py', 'tools/mini_host_journal.py', 'tools/start_mini_admin_session.ps1')) {
    $path = Join-Path $workspace $name
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $config.source_pins.$name) {
        throw ('Broker source changed: ' + $name)
    }
}
$broker = Join-Path $workspace 'tools/mini_admin_session.py'
$arguments = @('-I', '-B', '-X', 'utf8', ('"' + $broker + '"'), 'serve', '--session', $Session, '--session-sha', $SessionSHA)
# One UAC elevation only. No services/tasks/policies or arbitrary shell payloads.
$process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $workspace -Verb RunAs -WindowStyle Hidden -PassThru
Write-Output ('HyperRig administrative session PID ' + $process.Id)
