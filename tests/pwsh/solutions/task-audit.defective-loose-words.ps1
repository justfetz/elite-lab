# A plausible but wrong solution: it matches pieces of the rules instead of the rules. Any
# "hidden" in the arguments counts, any "://" counts, and the folders are matched without
# the \ or % that closes them. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

foreach ($task in (Import-Csv -LiteralPath (Join-Path $Path 'tasks.csv'))) {
    $program = ([string]$task.Execute).Trim().Trim('"')
    $arguments = [string]$task.Arguments
    $risky = $program -match '^(C:\\Users|C:\\ProgramData|C:\\Windows\\Temp|%TEMP|%APPDATA|%LOCALAPPDATA|%PUBLIC)'
    if ($arguments -match '(^|\s)-(e|enc|encodedcommand)(\s|$)' -or $arguments -match 'hidden') {
        $risky = $true
    }
    if ($arguments -match '://') {
        $risky = $true
    }
    if ($risky) {
        $task.TaskName
    }
}
