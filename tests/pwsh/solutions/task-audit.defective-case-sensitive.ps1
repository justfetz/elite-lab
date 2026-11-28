# A plausible but wrong solution: it looks for the spellings of rule 2 exactly as the brief
# prints them, with String.Contains: case matters to it, and a word that only begins like
# -enc counts. The checker must fail it.
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
    if ($arguments.Contains('-EncodedCommand') -or $arguments.Contains('-enc') -or $arguments.Contains('-e ') -or
        $arguments.Contains('-WindowStyle Hidden') -or $arguments.Contains('-w hidden')) {
        $risky = $true
    }
    if ($arguments -match 'https?://') {
        $risky = $true
    }
    if ($risky) {
        $task.TaskName
    }
}
