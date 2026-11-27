# A plausible but wrong solution: it finds every risky task, and prints a task once for
# every rule the task breaks instead of once. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$writable = 'C:\Users\', 'C:\ProgramData\', 'C:\Windows\Temp\', '%TEMP%', '%APPDATA%', '%LOCALAPPDATA%', '%PUBLIC%'

foreach ($task in (Import-Csv -LiteralPath (Join-Path $Path 'tasks.csv'))) {
    $program = ([string]$task.Execute).Trim().Trim('"')
    $arguments = [string]$task.Arguments
    foreach ($prefix in $writable) {
        if ($program.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            $task.TaskName
        }
    }
    if ($arguments -match '(^|\s)-(e|enc|encodedcommand)(\s|$)' -or $arguments -match '(^|\s)-(w|windowstyle)\s+hidden(\s|$)') {
        $task.TaskName
    }
    if ($arguments -match 'https?://') {
        $task.TaskName
    }
}
