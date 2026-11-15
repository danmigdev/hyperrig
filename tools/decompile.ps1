param([ValidateSet('tank-g-v1','tank-g-v2','tank-b-v1','tank-b-v2','tank-mini')][string]$Target = 'tank-g-v2')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskGhidra = Join-Path $PSScriptRoot 'vendor\ghidra_12.2_PUBLIC'
$taskProfiles = @{
    'tank-g-v1' = 'analysis\firmware\m571_v1_app\app.bin'
    'tank-g-v2' = 'analysis\firmware\m571_g_app\app.bin'
    'tank-b-v1' = 'analysis\firmware\m571_tbv1_app\app.bin'
    'tank-b-v2' = 'analysis\firmware\m571_tb_app\app.bin'
    'tank-mini' = 'analysis\tank-mini\app.bin'
}
$taskBinary = Join-Path $taskRoot $taskProfiles[$Target]
$taskLayout = Get-Content -LiteralPath (Join-Path (Split-Path $taskBinary -Parent) 'memory-layout.json') -Raw | ConvertFrom-Json
$taskProjects = Join-Path $taskRoot 'analysis\ghidra'
New-Item -ItemType Directory -Force -Path $taskProjects | Out-Null
& "$taskGhidra\support\analyzeHeadless.bat" $taskProjects $Target `
    -import $taskBinary -overwrite `
    -processor 'pi32v2:LE:32:default' -loader BinaryLoader -loader-baseAddr '0x02000120' `
    -scriptPath (Join-Path $PSScriptRoot 'ghidra') `
    -preScript MapFirmware.java ("0x{0:x}" -f $taskLayout.ram_source) ("0x{0:x}" -f $taskLayout.ram_size) `
    -analysisTimeoutPerFile 180 -max-cpu 2 `
    -postScript ExportRecovered.java (Join-Path $taskRoot "recovered\ghidra\$Target") `
    -log (Join-Path $taskProjects "$Target.log")
exit $LASTEXITCODE
