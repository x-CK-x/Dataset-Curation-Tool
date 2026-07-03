param([int]$Port = 7865)
$pids = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if (-not $pids) {
    Write-Host "No Data Curation Tool server is listening on port $Port."
    exit 0
}
foreach ($pidValue in $pids) {
    $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "Stopping PID $pidValue - $($proc.ProcessName)"
        Stop-Process -Id $pidValue -Force
    }
}
