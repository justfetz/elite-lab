# A plausible but wrong solution: correct in every respect but one. It looks for
# -WindowStyle Hidden and never for the short spelling, -w hidden. The checker must fail it.
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
    if ($arguments -match '(^|\s)-windowstyle\s+hidden(\s|$)') {
        $risky = $true
    }
    if ($arguments -match 'https?://') {
        $risky = $true
    }
    if ($risky) {
        $task.TaskName
    }
}
