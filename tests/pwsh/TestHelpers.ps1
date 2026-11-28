# Shared helpers for the Pester suites. Dot-source this file in BeforeAll:
#
#   BeforeAll { . (Join-Path $PSScriptRoot 'TestHelpers.ps1') }
#
# Everything here builds its fixtures under the folder it is given (the suites pass
# Pester's TestDrive), and nothing reads or changes the machine outside it.

function Get-TestRepoRoot {
    # The root of the clone these tests live in.
    [CmdletBinding()]
    [OutputType([string])]
    param()
    return (Resolve-Path -LiteralPath (Join-Path (Join-Path $PSScriptRoot '..') '..')).ProviderPath
}

function Test-OnWindows {
    # True on Windows, in Windows PowerShell 5.1 and in PowerShell 7 alike.
    [CmdletBinding()]
    [OutputType([bool])]
    param()
    return [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
}

function Import-TestModule {
    # Loads EliteLab from a clone (this one by default), replacing any copy already loaded.
    [CmdletBinding()]
    param(
        [string] $From = (Get-TestRepoRoot)
    )
    Get-Module -Name EliteLab | Remove-Module -Force
    Import-Module (Join-Path (Join-Path $From 'pwsh') 'EliteLab') -Force
}

function Get-TestText {
    # Non-ASCII text for the tests, built from code points: these files stay ASCII,
    # because Windows PowerShell 5.1 reads a script without a byte-order mark as ANSI.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('UserName', 'Sentence', 'EmDash')]
        [string] $Name
    )
    switch ($Name) {
        'UserName' { return 'Zo{0} M{1}ller' -f [char]0x00EB, [char]0x00FC }
        'Sentence' { return 'caf{0} {1} {2}{3}{4} {5}' -f [char]0x00E9, [char]0x2014, [char]0x65E5, [char]0x672C, [char]0x8A9E, [char]0x2713 }
        'EmDash' { return [string][char]0x2014 }
    }
}

function Get-TestShownText {
    # Everything a command writes for the learner (its output and its information
    # stream) as one line of text with single spaces. Out-String would wrap long lines
    # at the width of the console, which differs from one PowerShell to the next.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [scriptblock] $Command
    )
    $lines = @(& $Command 6>&1 | ForEach-Object { [string]$_ })
    return (($lines -join ' ') -replace '\s+', ' ').Trim()
}

function Copy-TestClone {
    # Builds a clone of the repository's runtime files at $Destination.
    # With -StubCli the Python package is replaced by a stand-in that reports what it
    # was given, so the wrapper can be tested apart from the real CLI.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Destination,

        [switch] $StubCli
    )
    $root = Get-TestRepoRoot
    $null = New-Item -ItemType Directory -Path $Destination -Force
    Copy-Item -LiteralPath (Join-Path $root 'pwsh') -Destination $Destination -Recurse -Force
    if ($StubCli) {
        $package = Join-Path $Destination 'elitelab'
        $null = New-Item -ItemType Directory -Path $package -Force
        $ascii = New-Object System.Text.ASCIIEncoding
        [System.IO.File]::WriteAllText((Join-Path $package '__init__.py'), "__version__ = 'stub'`n", $ascii)
        $stub = @'
"""Stand-in for elitelab.cli in the wrapper tests: it reports what it was given."""
import json
import os
import sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["--exit"]:
        sys.exit(int(argv[1]))
    if argv[:1] == ["--stderr-then-exit"]:
        sys.stderr.write("stub: this went to stderr\n")
        print("stub: this went to stdout")
        sys.exit(int(argv[1]))
    if argv[:1] == ["--utf8"]:
        print("caf\u00e9 \u2014 \u65e5\u672c\u8a9e \u2713")
        return
    if argv[:1] == ["--stdin"]:
        print("stdin=" + json.dumps(sys.stdin.read()))
        return
    if argv[:1] == ["--env"]:
        print(json.dumps(dict((name, os.environ.get(name)) for name in argv[1:])))
        return
    if argv[:1] == ["doctor"]:
        sys.stderr.write("stub: doctor fell over\n")
        sys.exit(5)
    print(json.dumps({"argv": argv}))
'@
        [System.IO.File]::WriteAllText((Join-Path $package 'cli.py'), ($stub -replace "`r`n", "`n") + "`n", $ascii)
    }
    else {
        foreach ($name in 'elitelab', 'modules', 'drills') {
            Copy-Item -LiteralPath (Join-Path $root $name) -Destination $Destination -Recurse -Force
        }
        Copy-Item -LiteralPath (Join-Path $root 'elite.py') -Destination $Destination -Force
    }
    return $Destination
}

function Write-FakePython {
    # Puts a stand-in interpreter named $Name in $Directory. It ignores its arguments,
    # prints $Output and exits with $ExitCode: enough to play "a Python of version X".
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Directory,

        [Parameter(Mandatory = $true)]
        [string] $Name,

        [string] $Output = '',

        [int] $ExitCode = 0
    )
    $null = New-Item -ItemType Directory -Path $Directory -Force
    $ascii = New-Object System.Text.ASCIIEncoding
    if (Test-OnWindows) {
        $path = Join-Path $Directory ($Name + '.cmd')
        $lines = @('@echo off')
        if ($Output) {
            $lines += 'echo ' + $Output
        }
        $lines += 'exit /b ' + $ExitCode
        [System.IO.File]::WriteAllText($path, ($lines -join "`r`n") + "`r`n", $ascii)
    }
    else {
        $path = Join-Path $Directory $Name
        $lines = @('#!/bin/sh')
        if ($Output) {
            $lines += "echo '" + $Output + "'"
        }
        $lines += 'exit ' + $ExitCode
        [System.IO.File]::WriteAllText($path, ($lines -join "`n") + "`n", $ascii)
        & /bin/chmod 755 $path
    }
    return $path
}

function Get-TestFileList {
    # Every file under $Path with its size and time stamp, to compare before and after.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [string[]] $Exclude = @('.git', '__pycache__', '.pytest_cache')
    )
    $root = (Resolve-Path -LiteralPath $Path).ProviderPath
    foreach ($file in (Get-ChildItem -LiteralPath $root -Recurse -File -Force)) {
        $relative = $file.FullName.Substring($root.Length).TrimStart('\', '/')
        $parts = $relative -split '[\\/]'
        if (@($parts | Where-Object { $Exclude -contains $_ }).Count -gt 0) {
            continue
        }
        '{0}|{1}|{2}' -f $relative, $file.Length, $file.LastWriteTimeUtc.Ticks
    }
}
