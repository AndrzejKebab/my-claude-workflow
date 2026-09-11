param(
    [string]$Filter = "",
    [switch]$Quiet,
    [switch]$Terminate
)

$matches = foreach ($process in Get-CimInstance Win32_Process -Filter "Name = 'Unity.exe'") {
    $commandLine = [string]$process.CommandLine
    if ($commandLine -match '(?i)-name\s+"?AssetImportWorker') {
        continue
    }
    $projectPath = ""
    if ($commandLine -match '(?i)-projectpath\s+(?:"([^"]+)"|(\S+))') {
        $projectPath = if ($Matches[1]) { $Matches[1] } else { $Matches[2] }
    }
    if (-not $projectPath) {
        continue
    }
    if ($Filter -and $projectPath.IndexOf($Filter, [StringComparison]::OrdinalIgnoreCase) -lt 0) {
        continue
    }
    [pscustomobject]@{
        ProcessId = [int]$process.ProcessId
        ProjectPath = $projectPath
    }
}

if (-not $matches) {
    exit 1
}

if ($Terminate) {
    foreach ($match in $matches) {
        Stop-Process -Id $match.ProcessId -Force
        "Stopped {0}`t{1}" -f $match.ProcessId, $match.ProjectPath
    }
    exit 0
}

if (-not $Quiet) {
    foreach ($match in $matches) {
        "{0}`t{1}" -f $match.ProcessId, $match.ProjectPath
    }
}
