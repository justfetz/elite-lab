# A plausible but wrong solution: it knows the rules but not every spelling of them. It
# never looks for -enc, %TEMP%, %LOCALAPPDATA% or %PUBLIC%, and it prints a task once for
# every rule the task breaks. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$writable = 'C:\Users\', 'C:\ProgramData\', 'C:\Windows\Temp\', '%APPDATA%'

foreach ($task in (Import-Csv -LiteralPath (Join-Path $Path 'tasks.csv'))) {
    $program = ([string]$task.Execute).Trim().Trim('"')
    $arguments = [string]$task.Arguments
    foreach ($prefix in $writable) {
        if ($program.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            $task.TaskName
        }
    }
    if ($arguments -match '(^|\s)-(e|encodedcommand)(\s|$)') {
        $task.TaskName
    }
    if ($arguments -match '(^|\s)-(w|windowstyle)\s+hidden(\s|$)') {
        $task.TaskName
    }
    if ($arguments -match 'https?://') {
        $task.TaskName
    }
}
