# A plausible but wrong solution: it matches loosely. -Encoding looks like -enc to it,
# httpd.conf looks like a URL, and a quoted path hides from it. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

foreach ($task in (Import-Csv -LiteralPath (Join-Path $Path 'tasks.csv'))) {
    if ($task.Execute -like 'C:\Users\*' -or $task.Execute -like 'C:\ProgramData\*' -or
        $task.Arguments -like '*-enc*' -or $task.Arguments -like '*http*') {
        $task.TaskName
    }
}
