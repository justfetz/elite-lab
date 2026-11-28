<#
.SYNOPSIS
Runs PSScriptAnalyzer over this repository with the committed settings.

.DESCRIPTION
The CI workflow and the Pester suite both call this script, so the repository is
linted one way everywhere:

    ./tests/pwsh/Invoke-Analyzer.ps1

The analysis runs in a child PowerShell of the same kind as the caller, with a time
limit. In CI the analyzer once stopped with "Object reference not set to an instance
of an object" before it had read a file, and then held the step for fifteen minutes.
An attempt that crashes or runs out of time is started again, up to -Attempts times.
Findings are never tried again: an attempt that finishes is the answer, whatever it
found.

Without -PassThru the script prints the findings and one summary line, and ends with
exit code 0 (nothing found), 1 (findings) or 2 (the analyzer did not finish).

.PARAMETER ModuleVersion
The PSScriptAnalyzer version to load. Without it the newest installed version is used.

.PARAMETER Attempts
How many times to start the analyzer before giving up. The default is 3.

.PARAMETER TimeoutSeconds
How long one attempt may take. The default is 300 seconds.

.PARAMETER PassThru
Return the findings as objects, and throw if the analyzer did not finish, instead of
printing a report and setting an exit code.

.PARAMETER WorkerOutFile
Used by the script itself: analyze in this process and write the result to this file.

.EXAMPLE
./tests/pwsh/Invoke-Analyzer.ps1

Prints "PSScriptAnalyzer 1.24.0: 31 files analyzed, 0 findings" when the code is clean.

.EXAMPLE
$findings = @(./tests/pwsh/Invoke-Analyzer.ps1 -PassThru)

Collects the findings without printing anything.
#>
[CmdletBinding()]
param(
    [string] $ModuleVersion = '',

    [ValidateRange(1, 10)]
    [int] $Attempts = 3,

    [ValidateRange(10, 3600)]
    [int] $TimeoutSeconds = 300,

    [switch] $PassThru,

    [string] $WorkerOutFile = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path -LiteralPath (Join-Path (Join-Path $PSScriptRoot '..') '..')).ProviderPath
$utf8 = New-Object System.Text.UTF8Encoding $false

if ($WorkerOutFile) {
    # --- one attempt, in this process ---------------------------------------------
    if ($ModuleVersion) {
        Import-Module -Name PSScriptAnalyzer -RequiredVersion $ModuleVersion
    }
    else {
        Import-Module -Name PSScriptAnalyzer
    }
    $extensions = '.ps1', '.psm1', '.psd1'
    $files = @(Get-ChildItem -LiteralPath $repoRoot -Recurse -File | Where-Object { $extensions -contains $_.Extension })
    $settings = Join-Path $repoRoot 'PSScriptAnalyzerSettings.psd1'
    # -Path takes wildcards, so a clone in a folder named like "lab [2]" has to be escaped
    $target = [System.Management.Automation.WildcardPattern]::Escape($repoRoot)
    $found = @(Invoke-ScriptAnalyzer -Path $target -Recurse -Settings $settings)
    $result = @{
        Version  = [string](Get-Module -Name PSScriptAnalyzer).Version
        Files    = $files.Count
        Findings = @($found | Sort-Object -Property ScriptPath, Line, RuleName | ForEach-Object {
                @{
                    File     = [string]$_.ScriptPath
                    Line     = [int]$_.Line
                    Severity = [string]$_.Severity
                    RuleName = [string]$_.RuleName
                    Message  = [string]$_.Message
                }
            })
    }
    [System.IO.File]::WriteAllText($WorkerOutFile, (ConvertTo-Json -InputObject $result -Depth 4), $utf8)
    exit 0
}

# --- the caller: start a worker, wait for it, start another if it did not finish --
if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) {
    $message = 'PSScriptAnalyzer is not installed. Install it with: Install-Module -Name PSScriptAnalyzer -Scope CurrentUser'
    if ($PassThru) {
        throw $message
    }
    $message
    exit 2
}
$hostPath = (Get-Process -Id $PID).Path
$outFile = Join-Path ([System.IO.Path]::GetTempPath()) ('elite-lab-analyzer-' + [guid]::NewGuid().ToString('N') + '.json')
$workerArguments = @('-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-WorkerOutFile', $outFile)
if ($ModuleVersion) {
    $workerArguments += @('-ModuleVersion', $ModuleVersion)
}

$result = $null
$problems = New-Object System.Collections.Generic.List[string]
$attempt = 0
try {
    while ($null -eq $result -and $attempt -lt $Attempts) {
        $attempt++
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = $hostPath
        $startInfo.WorkingDirectory = $repoRoot
        $startInfo.UseShellExecute = $false
        if ($null -ne $startInfo.PSObject.Properties['ArgumentList']) {
            foreach ($argument in $workerArguments) {
                $startInfo.ArgumentList.Add($argument)
            }
        }
        else {
            # Windows PowerShell: one command line, with quotes round what has a space in it
            $startInfo.Arguments = ($workerArguments | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '
        }
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        $problem = ''
        try {
            $null = $process.Start()
            if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
                try { $process.Kill() } catch { $null = $_ }
                $process.WaitForExit()
                $problem = 'ran for more than {0} seconds and was stopped' -f $TimeoutSeconds
            }
            elseif ($process.ExitCode -ne 0) {
                $problem = 'ended with exit code {0}' -f $process.ExitCode
            }
            elseif (-not (Test-Path -LiteralPath $outFile)) {
                $problem = 'ended without writing its result'
            }
        }
        finally {
            $process.Dispose()
        }
        if ($problem) {
            $problems.Add(('attempt {0} of {1} {2}' -f $attempt, $Attempts, $problem))
            Write-Warning -Message ('PSScriptAnalyzer did not finish: attempt {0} of {1} {2}.' -f $attempt, $Attempts, $problem)
            continue
        }
        $result = [System.IO.File]::ReadAllText($outFile, $utf8) | ConvertFrom-Json
    }
}
finally {
    if (Test-Path -LiteralPath $outFile) {
        Remove-Item -LiteralPath $outFile -Force
    }
}

if ($null -eq $result) {
    $message = 'PSScriptAnalyzer did not finish: ' + ($problems -join '; ') + '.'
    if ($PassThru) {
        throw $message
    }
    $message
    exit 2
}

$findings = @($result.Findings | ForEach-Object {
        [pscustomobject]@{
            File     = [string]$_.File
            Line     = [int]$_.Line
            Severity = [string]$_.Severity
            RuleName = [string]$_.RuleName
            Message  = [string]$_.Message
        }
    })

if ($PassThru) {
    $findings
    return
}

foreach ($finding in $findings) {
    $shown = $finding.File
    if ($shown.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        $shown = $shown.Substring($repoRoot.Length).TrimStart('\', '/')
    }
    '{0}:{1}  {2}  {3}  {4}' -f $shown, $finding.Line, $finding.Severity, $finding.RuleName, $finding.Message
}
$summary = 'PSScriptAnalyzer {0}: {1} files analyzed, {2} findings' -f $result.Version, $result.Files, $findings.Count
if ($attempt -gt 1) {
    $summary += ' (attempt {0} of {1}; the earlier ones did not finish)' -f $attempt, $Attempts
}
$summary
if ($findings.Count -gt 0) {
    exit 1
}
exit 0
