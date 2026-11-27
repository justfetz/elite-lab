# Reference solution for the task-audit checker. The tests prove it passes every case.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$writable = 'C:\Users\', 'C:\ProgramData\', 'C:\Windows\Temp\', '%TEMP%', '%APPDATA%', '%LOCALAPPDATA%', '%PUBLIC%'

foreach ($task in (Import-Csv -LiteralPath (Join-Path $Path 'tasks.csv'))) {
    $program = ([string]$task.Execute).Trim().Trim('"')
    $arguments = [string]$task.Arguments
    $risky = $false
    foreach ($prefix in $writable) {
        if ($program.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            $risky = $true
        }
    }
    if ($arguments -match '(^|\s)-(e|enc|encodedcommand)(\s|$)') {
        $risky = $true
    }
    if ($arguments -match '(^|\s)-(w|windowstyle)\s+hidden(\s|$)') {
        $risky = $true
    }
    if ($arguments -match 'https?://') {
        $risky = $true
    }
    if ($risky) {
        $task.TaskName
    }
}
