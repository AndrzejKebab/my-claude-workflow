# Kill Editors started by ONE lane, and only that lane's.
#
# Fleet rule (Manager, after two of the Reviewer's main-clone Editors were killed by other lanes'
# cleanup): kill only `Unity.exe` whose `-projectPath` is your own worktree. The main clone
# `F:/Unity/Projects/VoxelGame` belongs to the owner and the Reviewer and is never swept by a worker.
#
# So this matches the COMPLETE `-projectPath` argument, not a substring of the command line: a bare
# `-like '*path*'` would also match a longer path that starts with the same text, and would kill a
# lane that merely shares a prefix. Import workers (`-adb2 -name AssetImportWorkerHW…`) start with the
# same project path and are killed with it, deliberately - they are the same lane's Editor.
#
#   powershell -NoProfile -File kill_editors.ps1 -Project 'F:/Unity/Projects/VoxelGame-worker-5'
#   -> prints "killed N for <project>"
<#
.SYNOPSIS
Kill Editors whose -projectPath is exactly your own worktree, and no others: -Project <worktree>.
#>
param(
    [Parameter(Mandatory = $true)][string]$Project,
    # Report only: count this lane's Editors and kill nothing. Used by join_verify.sh, where a count
    # that quietly included other lanes' Editors read as "my cleanup left five behind".
    [switch]$Report
)

$wanted = [System.IO.Path]::GetFullPath($Project).TrimEnd('\', '/').Replace('/', '\')
$killed = 0
$skipped = 0

foreach ($process in Get-CimInstance Win32_Process -Filter "Name='Unity.exe'") {
    $commandLine = $process.CommandLine
    if ([string]::IsNullOrEmpty($commandLine)) { continue }

    # Split on -projectPath and take the token after it, so the comparison is against the whole path.
    $match = [regex]::Match($commandLine, '-projectPath\s+"?([^"\s]+)"?', 'IgnoreCase')
    if (-not $match.Success) { $skipped++; continue }

    $theirPath = $match.Groups[1].Value.Replace('/', '\').TrimEnd('\')

    if ([string]::Equals($theirPath, $wanted, [System.StringComparison]::OrdinalIgnoreCase)) {
        if ($Report) {
            $killed++
            continue
        }

        try {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
            # Print the pid: a kill without one cannot be disclosed properly afterwards, which is how
            # an incident report ends up saying "one Editor" instead of naming it.
            Write-Output "killed pid $($process.ProcessId) at $($process.CreationDate) for $theirPath"
            $killed++
        } catch {
            Write-Output "could not stop $($process.ProcessId): $($_.Exception.Message)"
        }
    } else {
        $skipped++
    }
}

if ($Report) {
    Write-Output $killed
} else {
    Write-Output "killed $killed for $wanted (left $skipped other Editors alone)"
}
