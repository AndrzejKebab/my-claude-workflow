# Kill players started from one executable path, and nothing else.
#
# Kept as a file rather than an inline -Command so there is no bash/PowerShell quoting layer between the
# intent and the filter: a single escaping mistake turns this into "kill nothing" and it fails silently,
# which is how an orphaned server ended up holding the fleet's single-seat box.
#
#   powershell -NoProfile -File kill_players.ps1 -Exe 'F:/path/to/VoxelGame.exe'
<#
.SYNOPSIS
Kill players started from one executable path, and nothing else: -Exe <path>. Prints "killed N from <path>".
#>
param(
    [Parameter(Mandatory = $true)][string]$Exe
)

$normalised = [System.IO.Path]::GetFullPath($Exe).Replace('/', '\')
$killed = 0

foreach ($process in Get-CimInstance Win32_Process -Filter "Name='VoxelGame.exe'") {
    if ([string]::IsNullOrEmpty($process.ExecutablePath)) { continue }

    if ([string]::Equals($process.ExecutablePath, $normalised, [System.StringComparison]::OrdinalIgnoreCase)) {
        try {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
            $killed++
        } catch {
            Write-Output "could not stop $($process.ProcessId): $($_.Exception.Message)"
        }
    }
}

Write-Output "killed $killed from $normalised"
