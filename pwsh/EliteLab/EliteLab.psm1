#Requires -Version 5.1

# EliteLab - the PowerShell side of elite-lab.
#
#   Invoke-Elite (alias: elite)   run the Python CLI from PowerShell
#   Test-EliteSetup               `elite doctor` as objects
#   Get-/Start-/Test-EliteChecker blue-team checkers: your script against fixture cases
#
# Works on Windows PowerShell 5.1 and PowerShell 7. Nothing here writes outside the
# temp folder; the only other file touched is the progress file the Python CLI keeps.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:BootstrapPath = Join-Path $PSScriptRoot 'elite_bootstrap.py'
$script:CompletionPath = Join-Path $PSScriptRoot 'EliteLab.Completions.json'
$script:CheckerFolder = Join-Path $PSScriptRoot 'Checkers'
$script:MinimumPython = [version]'3.8'
$script:PythonNames = @('py', 'python3', 'python')
$script:ArgvVariable = 'ELITELAB_ARGV'
$script:ExitNoPython = 127
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding $false
$script:OnWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
$script:OnMacOS = ($PSVersionTable.PSVersion.Major -ge 6) -and $IsMacOS
$script:PythonCache = $null
$script:CompletionData = $null
$script:CheckerTable = $null

#region Output

function Write-EliteLine {
    # Text for the learner. It goes to the information stream, so it shows on screen,
    # stays out of the pipeline, and can be silenced or captured with 6>.
    [CmdletBinding()]
    param(
        [Parameter(Position = 0)]
        [AllowEmptyString()]
        [string] $Text = ''
    )
    Write-Information -MessageData $Text -InformationAction Continue
}

function Format-EliteParagraph {
    # Wraps one paragraph to the width the Python CLI uses, with an indent on every line.
    [CmdletBinding()]
    [OutputType([string[]])]
    param(
        [AllowEmptyString()]
        [string] $Text = '',

        [string] $Indent = '',

        [string] $FirstIndent = $Indent,

        [int] $Width = 88
    )
    $lines = New-Object System.Collections.Generic.List[string]
    $current = $FirstIndent
    $empty = $true
    foreach ($word in ($Text -split '\s+' | Where-Object { $_ })) {
        if (-not $empty -and ($current.Length + 1 + $word.Length) -gt $Width) {
            $lines.Add($current)
            $current = $Indent
            $empty = $true
        }
        if ($empty) {
            $current += $word
        }
        else {
            $current += ' ' + $word
        }
        $empty = $false
    }
    if (-not $empty) {
        $lines.Add($current)
    }
    return $lines.ToArray()
}

#endregion

#region Python discovery

function Get-ElitePythonVersion {
    # The version of the Python at $Path, or $null when it does not run.
    [CmdletBinding()]
    [OutputType([version])]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path
    )
    # A native program writing to stderr must not become a terminating error here:
    # Windows PowerShell 5.1 turns redirected stderr into error records.
    $ErrorActionPreference = 'Continue'
    Set-Variable -Name PSNativeCommandUseErrorActionPreference -Value $false -Scope Local
    $printed = $null
    try {
        # No double quotes in this code on purpose: 5.1 would drop them on the way.
        $printed = & $Path -c 'import sys; v = sys.version_info; print(v[0], v[1], v[2])' 2>$null
    }
    catch {
        Write-Debug "elite: $Path did not start: $_"
        return $null
    }
    if ($LASTEXITCODE -ne 0) {
        return $null
    }
    # Python 3 prints "3 12 4"; Python 2 prints the tuple "(2, 7, 18)".
    if ((@($printed) -join ' ') -match '(\d+)\D+(\d+)\D+(\d+)') {
        return New-Object System.Version ([int]$Matches[1]), ([int]$Matches[2]), ([int]$Matches[3])
    }
    return $null
}

function Get-ElitePython {
    # Finds the Python that elite will use: the py launcher, then python3, then python.
    # The first one that is 3.8 or newer wins. The answer is cached until PATH changes.
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param()

    $key = '{0}|{1}' -f $env:PATH, $env:PATHEXT
    if ($null -ne $script:PythonCache -and $script:PythonCache.Key -eq $key) {
        return $script:PythonCache.Value
    }

    $seen = New-Object System.Collections.Generic.List[object]
    $chosen = $null
    foreach ($name in $script:PythonNames) {
        # Ignore, not SilentlyContinue: a Python that is not there must not land in $Error
        $command = Get-Command -Name $name -CommandType Application -ErrorAction Ignore |
            Select-Object -First 1
        if ($null -eq $command) {
            continue
        }
        $candidate = [pscustomobject]@{
            Name    = $name
            Path    = $command.Path
            Version = Get-ElitePythonVersion -Path $command.Path
        }
        $seen.Add($candidate)
        if ($null -ne $candidate.Version -and $candidate.Version -ge $script:MinimumPython) {
            $chosen = $candidate
            break
        }
    }

    if ($null -ne $chosen) {
        $problem = $null
        $shown = $chosen
    }
    else {
        $versioned = @($seen | Where-Object { $null -ne $_.Version } | Sort-Object -Property Version -Descending)
        if ($versioned.Count -gt 0) {
            $problem = 'old'
            $shown = $versioned[0]
        }
        elseif ($seen.Count -gt 0) {
            $problem = 'broken'
            $shown = $seen[0]
        }
        else {
            $problem = 'missing'
            $shown = [pscustomobject]@{ Name = $null; Path = $null; Version = $null }
        }
    }

    $result = [pscustomobject]@{
        Usable  = ($null -ne $chosen)
        Name    = $shown.Name
        Path    = $shown.Path
        Version = $shown.Version
        Problem = $problem
    }
    $script:PythonCache = @{ Key = $key; Value = $result }
    return $result
}

function Get-ElitePythonInstallCommand {
    # The one command that installs Python on this kind of machine.
    [CmdletBinding()]
    [OutputType([string])]
    param()
    if ($script:OnWindows) {
        return 'winget install --exact --id Python.Python.3.13'
    }
    if ($script:OnMacOS) {
        return 'brew install python'
    }
    return 'sudo apt install python3      (Fedora: sudo dnf install python3)'
}

function Get-ElitePythonAdvice {
    # What to tell a learner whose Python is missing, too old or broken. Plain lines.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Python
    )
    $need = 'Python {0} or newer' -f $script:MinimumPython
    switch ($Python.Problem) {
        'old' {
            $first = 'elite needs {0}. The newest one found is Python {1} ({2} at {3}).' -f
                $need, $Python.Version, $Python.Name, $Python.Path
        }
        'broken' {
            $first = 'elite needs {0}. ''{1}'' was found at {2} but it did not run.' -f
                $need, $Python.Name, $Python.Path
            if ($script:OnWindows) {
                $first += ' On Windows that is usually the Microsoft Store placeholder, not a real Python.'
            }
        }
        default {
            $first = 'elite needs {0}, and none was found on your PATH.' -f $need
        }
    }
    $first
    ''
    '  Install it:   {0}' -f (Get-ElitePythonInstallCommand)
    '  Then open a new PowerShell window and run:   elite doctor'
}

#endregion

#region Running the CLI

function ConvertTo-EliteArgument {
    # Turns a function's $args back into the words the learner typed.
    #
    # PowerShell parses a command line before a function sees it, and three of its
    # habits would change what Python receives:
    #   80,443     arrives as an array      -> joined again with ','
    #   -p:80      arrives as '-p:' and 80  -> joined again (PowerShell marks '-p:' as a
    #                                          parameter it split; a quoted '-p:' is left alone)
    #   0x10, 1.0  arrive as numbers        -> [string] gives back the text as typed
    # $null (an empty variable) is dropped, as it is for any native command.
    # The words are written one by one; collect them with @( ), which keeps an empty
    # string as a word and gives an empty array when there are none.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [AllowEmptyCollection()]
        [AllowNull()]
        [object[]] $ArgumentList = @()
    )
    $words = New-Object System.Collections.Generic.List[string]
    $pending = $null
    foreach ($item in @($ArgumentList)) {
        if ($null -eq $item) {
            continue
        }
        if ($item -is [System.Collections.IEnumerable] -and $item -isnot [string]) {
            $text = @($item | ForEach-Object { [string]$_ }) -join ','
        }
        else {
            $text = [string]$item
        }
        if ($null -ne $pending) {
            $words.Add($pending + $text)
            $pending = $null
            continue
        }
        $splitByParser = $false
        if ($item -is [string] -and $text.Length -gt 2 -and $text.StartsWith('-') -and $text.EndsWith(':')) {
            $splitByParser = $null -ne $item.psobject.Properties['<CommandParameterName>']
        }
        if ($splitByParser) {
            $pending = $text
        }
        else {
            $words.Add($text)
        }
    }
    if ($null -ne $pending) {
        $words.Add($pending)
    }
    foreach ($word in $words) {
        $word
    }
}

function ConvertTo-EliteArgv {
    # Encodes the words for elite_bootstrap.py: UTF-8, then base64, each closed with ';'.
    # They travel in an environment variable because no PowerShell before 7.3 can put a
    # double quote or an empty string on a native command line intact.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [AllowEmptyCollection()]
        [AllowEmptyString()]
        [string[]] $ArgumentList = @()
    )
    $builder = New-Object System.Text.StringBuilder
    foreach ($word in @($ArgumentList)) {
        $null = $builder.Append([System.Convert]::ToBase64String($script:Utf8NoBom.GetBytes([string]$word)))
        $null = $builder.Append(';')
    }
    return $builder.ToString()
}

function Enter-EliteEnvironment {
    # Sets what Python needs for one run and returns what was there before.
    [CmdletBinding()]
    [OutputType([hashtable])]
    param(
        [AllowEmptyString()]
        [string] $Argv = ''
    )
    $wanted = [ordered]@{
        $script:ArgvVariable = $Argv
        PYTHONUTF8           = '1'
        PYTHONIOENCODING     = 'utf-8'
    }
    $state = @{ Variables = @{}; ConsoleEncoding = $null }
    foreach ($name in $wanted.Keys) {
        $state.Variables[$name] = [System.Environment]::GetEnvironmentVariable($name)
        $value = $wanted[$name]
        if ([string]::IsNullOrEmpty($value)) {
            $value = $null      # no arguments: the variable is simply absent
        }
        [System.Environment]::SetEnvironmentVariable($name, $value)
    }
    # PowerShell decodes what a native program prints with the console's encoding.
    # Python is told to print UTF-8, so the console has to expect UTF-8 for this run.
    try {
        $current = [System.Console]::OutputEncoding
        if ($current.CodePage -ne 65001) {
            [System.Console]::OutputEncoding = $script:Utf8NoBom
            $state.ConsoleEncoding = $current
        }
    }
    catch {
        Write-Debug "elite: no console encoding to switch: $_"
    }
    return $state
}

function Exit-EliteEnvironment {
    # Puts back what Enter-EliteEnvironment changed.
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $State
    )
    foreach ($name in @($State.Variables.Keys)) {
        [System.Environment]::SetEnvironmentVariable($name, $State.Variables[$name])
    }
    if ($null -ne $State.ConsoleEncoding) {
        try {
            [System.Console]::OutputEncoding = $State.ConsoleEncoding
        }
        catch {
            Write-Debug "elite: could not restore the console encoding: $_"
        }
    }
}

function Invoke-EliteCapture {
    # Runs the CLI and captures what it prints. Used where the output is parsed.
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Python,

        [AllowEmptyCollection()]
        [AllowEmptyString()]
        [string[]] $ArgumentList = @()
    )
    $state = Enter-EliteEnvironment -Argv (ConvertTo-EliteArgv -ArgumentList $ArgumentList)
    try {
        $ErrorActionPreference = 'Continue'
        Set-Variable -Name PSNativeCommandUseErrorActionPreference -Value $false -Scope Local
        $all = @(& $Python.Path $script:BootstrapPath 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        Exit-EliteEnvironment -State $state
    }
    $output = New-Object System.Collections.Generic.List[string]
    $errors = New-Object System.Collections.Generic.List[string]
    foreach ($item in $all) {
        if ($item -is [System.Management.Automation.ErrorRecord]) {
            $errors.Add([string]$item.Exception.Message)      # a line Python wrote to stderr
        }
        else {
            $output.Add([string]$item)
        }
    }
    return [pscustomobject]@{
        ExitCode = $exitCode
        Output   = $output.ToArray()
        Error    = $errors.ToArray()
    }
}

function Invoke-Elite {
    <#
    .SYNOPSIS
    Runs the elite-lab command line from PowerShell.

    .DESCRIPTION
    Finds Python (the py launcher, then python3, then python), and runs the
    elite-lab CLI with every argument you typed, unchanged. Its alias is elite,
    so `elite doctor` in PowerShell does what `python3 elite.py doctor` does.

    The CLI's output is the only output. Its exit code is in $LASTEXITCODE
    afterwards, the way any program returns one: 0 for success, 2 for a usage
    error, and so on. When no usable Python is found the exit code is 127.

    If Python is missing or older than 3.8, you get a plain message with the
    command that installs it. Nothing is thrown.

    Text piped to the command becomes the CLI's input, so answers can be
    scripted: 'q' | elite learn networking

    One thing PowerShell itself takes before any function sees it: a bare --.
    Write it in quotes ('--') if the CLI must receive it.

    .EXAMPLE
    elite doctor

    Checks what is installed on this machine.

    .EXAMPLE
    elite lab submit wire-01 'flag{10.0.0.5:hunter2}'

    Submits a flag. Quote anything that holds braces, quotes or spaces.

    .EXAMPLE
    elite learn nosuchmodule; $LASTEXITCODE

    A failing subcommand prints the CLI's own error and leaves its exit code (2).

    .INPUTS
    System.String. Piped text is the CLI's standard input.

    .OUTPUTS
    System.String. The CLI's output, one line per string, when it is captured.

    .NOTES
    This function has no parameters of its own on purpose. A declared parameter
    would make PowerShell claim options such as -h and -sV before the CLI saw them.

    .LINK
    Test-EliteSetup
    #>
    $python = Get-ElitePython
    if (-not $python.Usable) {
        foreach ($line in (Get-ElitePythonAdvice -Python $python)) {
            Write-EliteLine $line
        }
        $global:LASTEXITCODE = $script:ExitNoPython
        return
    }

    $words = @(ConvertTo-EliteArgument -ArgumentList $args)
    $state = Enter-EliteEnvironment -Argv (ConvertTo-EliteArgv -ArgumentList $words)
    try {
        # Python's stderr (a usage error, say) must reach the screen as text and leave
        # the exit code alone, whatever the caller redirects.
        $ErrorActionPreference = 'Continue'
        Set-Variable -Name PSNativeCommandUseErrorActionPreference -Value $false -Scope Local
        Set-Variable -Name OutputEncoding -Value $script:Utf8NoBom -Scope Local
        if ($MyInvocation.ExpectingInput) {
            $input | & $python.Path $script:BootstrapPath
        }
        else {
            & $python.Path $script:BootstrapPath
        }
    }
    finally {
        Exit-EliteEnvironment -State $state
    }
}

#endregion

#region Tab completion

function Get-EliteCompletionData {
    # The tree pwsh/build_completions.py generated from elitelab.cli's own parser.
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param()
    if ($null -eq $script:CompletionData) {
        $text = [System.IO.File]::ReadAllText($script:CompletionPath, $script:Utf8NoBom)
        $script:CompletionData = ConvertFrom-Json -InputObject $text
    }
    return $script:CompletionData
}

function Get-ElitePositional {
    # The positional argument that the word at $Index belongs to, or $null.
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory = $true)]
        [psobject] $Node,

        [Parameter(Mandatory = $true)]
        [int] $Index
    )
    $start = 0
    foreach ($positional in @($Node.positionals)) {
        if ($positional.nargs -is [string] -and $positional.nargs -ne '?') {
            return $positional          # * + ... take every word that is left
        }
        $width = 1
        if ($positional.nargs -isnot [string]) {
            $width = [int]$positional.nargs
        }
        if ($Index -lt ($start + $width)) {
            return $positional
        }
        $start += $width
    }
    return $null
}

function Get-EliteCompletion {
    # Completions for one word of an elite command line, given the words before it.
    [CmdletBinding()]
    [OutputType([System.Management.Automation.CompletionResult])]
    param(
        [AllowEmptyString()]
        [string] $WordToComplete = '',

        [AllowEmptyCollection()]
        [AllowEmptyString()]
        [string[]] $PrecedingWord = @()
    )
    $node = Get-EliteCompletionData
    $index = 0
    $valueExpected = $false
    foreach ($word in @($PrecedingWord)) {
        if ($valueExpected) {
            $valueExpected = $false
            continue
        }
        if ($word.StartsWith('-')) {
            $option = @($node.options) | Where-Object { @($_.flags) -ccontains $word } | Select-Object -First 1
            if ($null -ne $option -and $option.takes_value) {
                $valueExpected = $true
            }
            continue
        }
        $child = $null
        if ($index -eq 0) {
            $child = @($node.commands) | Where-Object { $_.name -ceq $word } | Select-Object -First 1
        }
        if ($null -ne $child) {
            $node = $child
            $index = 0
            continue
        }
        $positional = Get-ElitePositional -Node $node -Index $index
        if ($null -ne $positional -and $positional.nargs -is [string] -and $positional.nargs -eq '...') {
            return      # the rest of the line belongs to another tool (elite run nmap ...)
        }
        $index++
    }
    if ($valueExpected) {
        return
    }

    $candidates = New-Object System.Collections.Generic.List[object]
    if ($WordToComplete.StartsWith('-')) {
        foreach ($option in @($node.options)) {
            foreach ($flag in @($option.flags)) {
                $candidates.Add(@{ Text = [string]$flag; Help = [string]$option.help })
            }
        }
    }
    elseif ($index -eq 0 -and @($node.commands).Count -gt 0) {
        foreach ($command in @($node.commands)) {
            $candidates.Add(@{ Text = [string]$command.name; Help = [string]$command.help })
        }
    }
    else {
        $positional = Get-ElitePositional -Node $node -Index $index
        if ($null -ne $positional -and $null -ne $positional.choices) {
            foreach ($choice in @($positional.choices)) {
                $candidates.Add(@{ Text = [string]$choice; Help = [string]$positional.help })
            }
        }
    }

    foreach ($candidate in $candidates) {
        if (-not $candidate.Text.StartsWith($WordToComplete, [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        $toolTip = $candidate.Help
        if ([string]::IsNullOrWhiteSpace($toolTip)) {
            $toolTip = $candidate.Text
        }
        New-Object System.Management.Automation.CompletionResult $candidate.Text, $candidate.Text, 'ParameterValue', $toolTip
    }
}

function Get-EliteCommandLineCompletion {
    # The body of the argument completer: reads the words before the cursor from the
    # command's syntax tree. A completer must never throw at the prompt, so it does not.
    [CmdletBinding()]
    [OutputType([System.Management.Automation.CompletionResult])]
    param(
        [AllowEmptyString()]
        [string] $WordToComplete = '',

        [System.Management.Automation.Language.CommandAst] $CommandAst,

        [int] $CursorPosition = 0
    )
    try {
        $preceding = New-Object System.Collections.Generic.List[string]
        $elements = @()
        if ($null -ne $CommandAst) {
            $elements = @($CommandAst.CommandElements)
        }
        for ($i = 1; $i -lt $elements.Count; $i++) {
            $element = $elements[$i]
            if ($element.Extent.EndOffset -ge $CursorPosition) {
                break       # this is the word being completed, or one after the cursor
            }
            if ($element -is [System.Management.Automation.Language.StringConstantExpressionAst]) {
                $preceding.Add([string]$element.Value)
            }
            else {
                $preceding.Add([string]$element.Extent.Text)
            }
        }
        Get-EliteCompletion -WordToComplete $WordToComplete -PrecedingWord $preceding.ToArray()
    }
    catch {
        Write-Debug "elite: completion failed: $_"
    }
}

#endregion

#region elite doctor as objects

function ConvertFrom-EliteDoctorOutput {
    # Parses the text `elite doctor` prints into one object per check.
    [CmdletBinding()]
    [OutputType('EliteLab.SetupCheck')]
    param(
        [AllowEmptyCollection()]
        [AllowEmptyString()]
        [string[]] $Line = @()
    )
    $checks = New-Object System.Collections.Generic.List[object]
    $install = @{}
    $group = 'Core'
    $inInstall = $false
    foreach ($text in @($Line)) {
        if ($text -match '^\s*\[(ok|--|!!)\]\s+(.+?)\s*$') {
            $mark = $Matches[1]
            $rest = $Matches[2]
            $name = $rest
            $detail = ''
            if ($group -eq 'Core' -and $rest -match '^(\S+)\s+(.+)$') {
                $name = $Matches[1]
                $detail = $Matches[2] -replace '\s+', ' '
            }
            elseif ($rest -match '^(.+?)\s+for:\s+(.*)$') {
                $name = $Matches[1]
                $detail = $Matches[2]
            }
            elseif ($rest -match '^(\S+)\s+(.+)$') {
                $name = $Matches[1]
                $detail = $Matches[2]
            }
            $status = 'ok'
            if ($mark -eq '--') {
                $status = 'missing'
            }
            elseif ($mark -eq '!!') {
                $status = 'problem'
            }
            $checks.Add([pscustomobject]@{
                    PSTypeName = 'EliteLab.SetupCheck'
                    Name       = $name
                    Ok         = ($mark -eq 'ok')
                    Status     = $status
                    Group      = $group
                    Required   = ($group -eq 'Core')
                    Detail     = $detail
                    Install    = ''
                })
        }
        elseif ($text -match '^\s{2}(\S.*):\s*$') {
            $header = $Matches[1]
            $inInstall = $false
            if ($header -like 'External tools*') {
                $group = 'External tools'
            }
            elseif ($header -like '*study_books*') {
                $group = 'Book tutor'
            }
            elseif ($header -like 'To install*') {
                $inInstall = $true
            }
            else {
                $group = $header
            }
        }
        elseif ($inInstall -and $text -match '^\s*-\s+(.+?):\s+(.+?)\s*$') {
            $install[$Matches[1]] = $Matches[2]
        }
    }
    foreach ($check in $checks) {
        if (-not $check.Ok -and $install.ContainsKey($check.Name)) {
            $check.Install = $install[$check.Name]
        }
        $check
    }
}

function Test-EliteSetup {
    <#
    .SYNOPSIS
    Checks this machine for elite-lab and returns one object per check.

    .DESCRIPTION
    Runs `elite doctor` and turns what it prints into objects, so the result can
    be filtered, sorted and tested instead of read.

    Each object has: Name, Ok (true or false), Status (ok, missing or problem),
    Group (Core, External tools or Book tutor), Required (only Python is),
    Detail (what the check is for) and Install (the command that installs a
    missing tool, when the CLI knows one).

    When Python itself is missing or older than 3.8 the CLI cannot run, so the
    result is a single Python check with Ok false and the install command.
    Nothing is thrown.

    .EXAMPLE
    Test-EliteSetup

    Lists every check with its verdict.

    .EXAMPLE
    Test-EliteSetup | Where-Object { -not $_.Ok } | Select-Object Name, Install

    Shows only what is missing, with the command that installs each one.

    .EXAMPLE
    if (Test-EliteSetup | Where-Object { $_.Required -and -not $_.Ok }) { 'not ready' }

    Tests whether anything the course cannot run without is missing.

    .INPUTS
    None.

    .OUTPUTS
    EliteLab.SetupCheck. One object per check.

    .LINK
    Invoke-Elite
    #>
    [CmdletBinding()]
    [OutputType('EliteLab.SetupCheck')]
    param()

    $python = Get-ElitePython
    if (-not $python.Usable) {
        $advice = @(Get-ElitePythonAdvice -Python $python)
        $status = 'missing'
        if ($python.Problem -ne 'missing') {
            $status = 'problem'
        }
        return [pscustomobject]@{
            PSTypeName = 'EliteLab.SetupCheck'
            Name       = 'Python'
            Ok         = $false
            Status     = $status
            Group      = 'Core'
            Required   = $true
            Detail     = $advice[0]
            Install    = Get-ElitePythonInstallCommand
        }
    }

    $run = Invoke-EliteCapture -Python $python -ArgumentList @('doctor')
    $checks = @(ConvertFrom-EliteDoctorOutput -Line $run.Output)
    if ($run.ExitCode -ne 0 -or $checks.Count -eq 0) {
        $reason = 'elite doctor exited with code {0}' -f $run.ExitCode
        $lastError = @($run.Error | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) | Select-Object -Last 1
        if ($null -ne $lastError) {
            $reason = '{0}: {1}' -f $reason, $lastError.Trim()
        }
        return [pscustomobject]@{
            PSTypeName = 'EliteLab.SetupCheck'
            Name       = 'elite doctor'
            Ok         = $false
            Status     = 'problem'
            Group      = 'Core'
            Required   = $true
            Detail     = $reason
            Install    = ''
        }
    }
    foreach ($check in $checks) {
        $check
    }
}

#endregion

#region Blue-team checkers

function Get-EliteTempRoot {
    # Everything the checkers write goes under this one folder in the temp folder.
    [CmdletBinding()]
    [OutputType([string])]
    param()
    return Join-Path ([System.IO.Path]::GetTempPath()) 'elite-lab'
}

function Write-EliteTextFile {
    # Writes a fixture file as UTF-8 without a byte-order mark, creating its folder.
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [AllowEmptyString()]
        [string] $Text = ''
    )
    $folder = Split-Path -Parent $Path
    if (-not [string]::IsNullOrEmpty($folder) -and -not (Test-Path -LiteralPath $folder)) {
        $null = [System.IO.Directory]::CreateDirectory($folder)
    }
    [System.IO.File]::WriteAllText($Path, $Text, $script:Utf8NoBom)
}

function Get-EliteCheckerTable {
    # Loads the checker definitions once: one .ps1 per checker in Checkers/, each
    # returning a hashtable. A definition is data plus the script block that builds
    # its fixture, so a new checker is a new file and nothing else.
    [CmdletBinding()]
    [OutputType([System.Collections.Specialized.OrderedDictionary])]
    param()
    if ($null -ne $script:CheckerTable) {
        return $script:CheckerTable
    }
    $required = 'Id', 'Title', 'Goal', 'ScriptName', 'Brief', 'Starter', 'Debrief', 'Build', 'Sample', 'Cases'
    $table = [ordered]@{}
    foreach ($file in (Get-ChildItem -LiteralPath $script:CheckerFolder -Filter '*.ps1' | Sort-Object -Property Name)) {
        $definition = & $file.FullName
        if ($definition -isnot [hashtable]) {
            throw "Checker file $($file.Name) did not return a hashtable."
        }
        foreach ($key in $required) {
            if (-not $definition.ContainsKey($key)) {
                throw "Checker file $($file.Name) has no '$key'."
            }
        }
        $table[$definition.Id] = $definition
    }
    $script:CheckerTable = $table
    return $table
}

function Resolve-EliteChecker {
    # The definition for $Id, or a plain "unknown checker" error raised for the caller.
    [CmdletBinding()]
    [OutputType([hashtable])]
    param(
        [Parameter(Mandatory = $true)]
        [string] $Id,

        [Parameter(Mandatory = $true)]
        [System.Management.Automation.PSCmdlet] $Cmdlet
    )
    $table = Get-EliteCheckerTable
    if ($table.Contains($Id)) {
        return $table[$Id]
    }
    $message = "There is no checker named '{0}'. The checkers are: {1}." -f $Id, (@($table.Keys) -join ', ')
    $record = New-Object System.Management.Automation.ErrorRecord (
        (New-Object System.ArgumentException $message), 'EliteLab.UnknownChecker',
        [System.Management.Automation.ErrorCategory]::ObjectNotFound, $Id)
    $Cmdlet.ThrowTerminatingError($record)
}

function Get-EliteCheckerCase {
    # The cases of a checker that apply on this platform.
    [CmdletBinding()]
    [OutputType([hashtable])]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Definition
    )
    $platform = 'Unix'
    if ($script:OnWindows) {
        $platform = 'Windows'
    }
    foreach ($case in @($Definition.Cases)) {
        if (-not $case.ContainsKey('Platform') -or $case.Platform -eq $platform) {
            $case
        }
    }
}

function Get-EliteCheckerBrief {
    # The rules of a checker as lines of text, with this platform's part included.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Definition
    )
    $extra = 'BriefUnix'
    if ($script:OnWindows) {
        $extra = 'BriefWindows'
    }
    foreach ($line in @($Definition.Brief)) {
        [string]$line
    }
    if ($Definition.ContainsKey($extra)) {
        foreach ($line in @($Definition[$extra])) {
            [string]$line
        }
    }
}

function Get-EliteCheckerPath {
    # Where a checker's workspace, starter script and sample fixture live.
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Definition
    )
    $workspace = Join-Path (Join-Path (Get-EliteTempRoot) 'checkers') $Definition.Id
    return [pscustomobject]@{
        Workspace = $workspace
        Script    = Join-Path $workspace $Definition.ScriptName
        Sample    = Join-Path $workspace 'sample'
        StartHere = Join-Path $workspace 'START_HERE.txt'
    }
}

function Get-EliteHostPath {
    # The PowerShell that is running this module, to run the learner's script with.
    [CmdletBinding()]
    [OutputType([string])]
    param()
    $name = 'powershell'
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        $name = 'pwsh'
    }
    if ($script:OnWindows) {
        $name += '.exe'
    }
    $candidate = Join-Path $PSHOME $name
    if (Test-Path -LiteralPath $candidate) {
        return $candidate
    }
    return (Get-Process -Id $PID).Path
}

function Invoke-EliteScript {
    # Runs the learner's script against one fixture case, in its own PowerShell process:
    # a crash, an `exit`, or a script that never ends cannot hurt this session.
    [CmdletBinding()]
    [OutputType([pscustomobject])]
    param(
        [Parameter(Mandatory = $true)]
        [string] $ScriptPath,

        [Parameter(Mandatory = $true)]
        [string] $CasePath,

        [int] $TimeoutSeconds = 60
    )
    # What the child PowerShell runs. Any error stops the script and is reported as one
    # plain line on stderr, the same on 5.1 and on 7; an `exit n` in the script is passed on.
    $template = @'
$ProgressPreference = 'SilentlyContinue'
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false } catch { $null = $_ }
$global:LASTEXITCODE = 0
try {
    & <SCRIPT> -Path <CASE>
}
catch {
    $where = ''
    if ($_.InvocationInfo -and $_.InvocationInfo.ScriptLineNumber) {
        $where = ' (line ' + $_.InvocationInfo.ScriptLineNumber + ')'
    }
    [Console]::Error.WriteLine(([string]$_.Exception.Message) + $where)
    exit 1
}
exit $LASTEXITCODE
'@
    # The two paths go in as single-quoted PowerShell strings, and the whole command goes
    # over as -EncodedCommand, so no quoting rule of any shell or version applies to them.
    $quote = { param($text) "'" + [System.Management.Automation.Language.CodeGeneration]::EscapeSingleQuotedStringContent($text) + "'" }
    $command = $template.Replace('<SCRIPT>', (& $quote $ScriptPath)).Replace('<CASE>', (& $quote $CasePath))
    $encoded = [System.Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($command))

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = Get-EliteHostPath
    $startInfo.Arguments = '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -OutputFormat Text -EncodedCommand ' + $encoded
    $startInfo.WorkingDirectory = $CasePath
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardInput = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.StandardOutputEncoding = $script:Utf8NoBom
    $startInfo.StandardErrorEncoding = $script:Utf8NoBom

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    $timedOut = $false
    $output = ''
    $errorText = ''
    $exitCode = -1
    try {
        $null = $process.Start()
        $process.StandardInput.Close()
        $outputTask = $process.StandardOutput.ReadToEndAsync()
        $errorTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            $timedOut = $true
            try {
                $process.Kill()
            }
            catch {
                Write-Debug "elite: the script's process had already ended: $_"
            }
        }
        if ($outputTask.Wait(5000)) {
            $output = [string]$outputTask.Result
        }
        if ($errorTask.Wait(5000)) {
            $errorText = [string]$errorTask.Result
        }
        if (-not $timedOut) {
            $process.WaitForExit()
            $exitCode = $process.ExitCode
        }
    }
    finally {
        $process.Dispose()
    }
    return [pscustomobject]@{
        ExitCode = $exitCode
        TimedOut = $timedOut
        Output   = @($output -split '\r?\n')
        Error    = $errorText
    }
}

function ConvertTo-EliteFinding {
    # One printed line as a comparable finding: trimmed, or the checker's own form of it
    # (the permission audit accepts a path with either slash, relative or full).
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Definition,

        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $Line,

        [Parameter(Mandatory = $true)]
        [string] $CasePath
    )
    if ($Definition.ContainsKey('Normalize')) {
        return [string](& $Definition.Normalize $Line $CasePath)
    }
    return $Line.Trim()
}

function Test-EliteCheckerCase {
    # Builds one fixture case, runs the script against it and compares the findings.
    [CmdletBinding()]
    [OutputType('EliteLab.CheckerCase')]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Definition,

        [Parameter(Mandatory = $true)]
        [hashtable] $Case,

        [Parameter(Mandatory = $true)]
        [string] $ScriptPath,

        [Parameter(Mandatory = $true)]
        [string] $CasePath,

        [int] $TimeoutSeconds = 60
    )
    $null = [System.IO.Directory]::CreateDirectory($CasePath)
    $null = & $Definition.Build $CasePath $Case $Definition

    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $run = Invoke-EliteScript -ScriptPath $ScriptPath -CasePath $CasePath -TimeoutSeconds $TimeoutSeconds
    $timer.Stop()

    $expected = @($Case.Expected | ForEach-Object { ConvertTo-EliteFinding -Definition $Definition -Line ([string]$_) -CasePath $CasePath })
    $actual = New-Object System.Collections.Generic.List[string]
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($line in $run.Output) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        $finding = ConvertTo-EliteFinding -Definition $Definition -Line $line -CasePath $CasePath
        if ($seen.Add($finding)) {
            $actual.Add($finding)
        }
    }
    $wanted = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($item in $expected) {
        $null = $wanted.Add($item)
    }
    $missed = @($expected | Where-Object { -not $seen.Contains($_) })
    $unexpected = @($actual | Where-Object { -not $wanted.Contains($_) })

    $ran = (-not $run.TimedOut) -and ($run.ExitCode -eq 0)
    $passed = $ran -and ($missed.Count -eq 0) -and ($unexpected.Count -eq 0)
    $detail = ''
    if ($run.TimedOut) {
        $detail = 'the script was still running after {0} seconds and was stopped' -f $TimeoutSeconds
    }
    elseif (-not $ran) {
        $firstError = @($run.Error -split '\r?\n' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) | Select-Object -First 1
        $detail = 'the script failed (exit code {0})' -f $run.ExitCode
        if ($null -ne $firstError) {
            $detail = '{0}: {1}' -f $detail, $firstError.Trim()
        }
    }
    elseif (-not $passed) {
        $parts = @()
        if ($missed.Count -gt 0) {
            $parts += 'missed: ' + (Format-EliteList -Item $missed)
        }
        if ($unexpected.Count -gt 0) {
            $parts += 'should not be flagged: ' + (Format-EliteList -Item $unexpected)
        }
        $detail = $parts -join '; '
    }
    $verdict = 'FAIL'
    if ($passed) {
        $verdict = 'pass'
    }
    return [pscustomobject]@{
        PSTypeName = 'EliteLab.CheckerCase'
        Checker    = $Definition.Id
        Case       = $Case.Name
        Passed     = $passed
        Verdict    = $verdict
        Detail     = $detail
        Why        = [string]$Case.Why
        Expected   = $expected
        Actual     = $actual.ToArray()
        Missed     = $missed
        Unexpected = $unexpected
        ExitCode   = $run.ExitCode
        Seconds    = [math]::Round($timer.Elapsed.TotalSeconds, 2)
    }
}

function Format-EliteList {
    # 'a, b, c' - or the first five and a count, so one bad script cannot flood the screen.
    [CmdletBinding()]
    [OutputType([string])]
    param(
        [AllowEmptyCollection()]
        [string[]] $Item = @()
    )
    $shown = @($Item | Select-Object -First 5)
    $text = $shown -join ', '
    if ($Item.Count -gt $shown.Count) {
        $text = '{0} and {1} more' -f $text, ($Item.Count - $shown.Count)
    }
    return $text
}

function Get-EliteChecker {
    <#
    .SYNOPSIS
    Lists the blue-team checkers.

    .DESCRIPTION
    A checker is a small defensive job: you write a PowerShell audit script, and
    the checker runs it against fixture cases and shows a verdict for each one.
    The fixtures are files in the temp folder. A checker never reads or changes
    the real system: no registry, no services, no network, no admin rights.

    Each object has the checker's Id, Title and Goal, how many Cases it runs on
    this platform, and the paths of its Workspace and Script (where
    Start-EliteChecker puts the starter script).

    .PARAMETER Id
    The checker to show. Leave it out to list them all.

    .EXAMPLE
    Get-EliteChecker

    Lists every checker.

    .EXAMPLE
    Get-EliteChecker -Id task-audit | Format-List

    Shows one checker in full, with the path of its workspace.

    .INPUTS
    None.

    .OUTPUTS
    EliteLab.Checker.

    .LINK
    Start-EliteChecker

    .LINK
    Test-EliteChecker
    #>
    [CmdletBinding()]
    [OutputType('EliteLab.Checker')]
    param(
        [Parameter(Position = 0)]
        [string] $Id
    )
    $definitions = @()
    if ([string]::IsNullOrEmpty($Id)) {
        $definitions = @((Get-EliteCheckerTable).Values)
    }
    else {
        $definitions = @(Resolve-EliteChecker -Id $Id -Cmdlet $PSCmdlet)
    }
    foreach ($definition in $definitions) {
        $paths = Get-EliteCheckerPath -Definition $definition
        [pscustomobject]@{
            PSTypeName = 'EliteLab.Checker'
            Id         = $definition.Id
            Title      = $definition.Title
            Goal       = $definition.Goal
            Cases      = @(Get-EliteCheckerCase -Definition $definition).Count
            Workspace  = $paths.Workspace
            Script     = $paths.Script
        }
    }
}

function Start-EliteChecker {
    <#
    .SYNOPSIS
    Sets up a blue-team checker: the brief, a starter script and a sample fixture.

    .DESCRIPTION
    Creates the checker's workspace under the temp folder and prints the brief:
    the goal, the exact rules, what your script receives and what it must print.

    The workspace holds START_HERE.txt (the brief), a starter script with the
    parameter already declared, and a sample/ fixture to explore with real
    commands. Your own script is never overwritten unless you pass -Force.

    The workspace is in the temp folder, which the system may clear. Keep your
    script somewhere of your own if you want it to last, and point
    Test-EliteChecker at it with -ScriptPath.

    .PARAMETER Id
    The checker to set up. Get-EliteChecker lists them.

    .PARAMETER Force
    Replace the starter script even if it already exists. Your edits are lost.

    .EXAMPLE
    Start-EliteChecker task-audit

    Sets up the scheduled-task audit and prints its brief.

    .EXAMPLE
    Start-EliteChecker perm-audit -Force

    Starts over with a fresh starter script.

    .INPUTS
    None.

    .OUTPUTS
    None. The brief is written to the information stream.

    .LINK
    Test-EliteChecker
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $Id,

        [switch] $Force
    )
    $definition = Resolve-EliteChecker -Id $Id -Cmdlet $PSCmdlet
    $paths = Get-EliteCheckerPath -Definition $definition

    $brief = @(
        ('{0}: {1}' -f $definition.Id, $definition.Title)
        ''
    )
    $brief += @(Format-EliteParagraph -Text $definition.Goal -FirstIndent 'GOAL   ' -Indent '       ')
    $brief += @(
        ''
        'THE RULES'
    )
    foreach ($line in (Get-EliteCheckerBrief -Definition $definition)) {
        if ([string]::IsNullOrEmpty($line)) {
            $brief += ''
        }
        else {
            $brief += '  ' + $line
        }
    }
    $brief += @(
        ''
        'YOUR SCRIPT'
        ('  {0}' -f $paths.Script)
        '  It receives  -Path <folder>  and prints one finding per line, nothing else.'
        '  It runs with $ErrorActionPreference = ''Stop'': an error fails the case.'
        ''
        'A SAMPLE TO EXPLORE'
        ('  {0}' -f $paths.Sample)
        ''
        'CHECK IT'
        ('  Test-EliteChecker {0}' -f $definition.Id)
        ''
        'This folder is in your temp folder, which the system may clear. Keep your'
        'script somewhere of your own and check it with:'
        ('  Test-EliteChecker {0} -ScriptPath <your script>' -f $definition.Id)
    )

    if ($PSCmdlet.ShouldProcess($paths.Workspace, 'Set up the checker workspace')) {
        $null = [System.IO.Directory]::CreateDirectory($paths.Workspace)
        if ($Force -or -not (Test-Path -LiteralPath $paths.Script)) {
            Write-EliteTextFile -Path $paths.Script -Text $definition.Starter
        }
        if (Test-Path -LiteralPath $paths.Sample) {
            Remove-Item -LiteralPath $paths.Sample -Recurse -Force
        }
        $null = [System.IO.Directory]::CreateDirectory($paths.Sample)
        $null = & $definition.Build $paths.Sample $definition.Sample $definition
        Write-EliteTextFile -Path $paths.StartHere -Text (($brief -join [System.Environment]::NewLine) + [System.Environment]::NewLine)
    }

    Write-EliteLine
    foreach ($line in $brief) {
        Write-EliteLine $line
    }
    Write-EliteLine
}

function Test-EliteChecker {
    <#
    .SYNOPSIS
    Runs your script against a checker's fixture cases and shows each verdict.

    .DESCRIPTION
    Builds every fixture case in a fresh folder under the temp folder, runs your
    script against each one in its own PowerShell process, and compares what the
    script printed with what the case holds. Every case is shown with its
    verdict. A failed case also says what was missed or wrongly flagged, and why
    that case exists. The fixture folders are removed afterwards.

    Each case is built so that one mistake fails it and nothing else does: a
    script that skips a rule passes the other cases and fails that one.

    A case fails if the script errors, exits with a code other than 0, runs
    longer than the time limit, or prints anything that is not a finding.

    .PARAMETER Id
    The checker to run. Get-EliteChecker lists them.

    .PARAMETER ScriptPath
    The script to check. The default is the starter script in the checker's
    workspace, which Start-EliteChecker creates.

    .PARAMETER TimeoutSeconds
    How long the script may run on one case before it is stopped. Default 60.

    .PARAMETER PassThru
    Also return one object per case: Case, Passed, Verdict, Detail, Expected,
    Actual, Missed, Unexpected, ExitCode and Seconds.

    .EXAMPLE
    Test-EliteChecker task-audit

    Checks the script in the task-audit workspace.

    .EXAMPLE
    Test-EliteChecker logon-burst -ScriptPath ~\scripts\Find-LogonBurst.ps1

    Checks a script you keep somewhere else.

    .EXAMPLE
    (Test-EliteChecker baseline-check -PassThru | Where-Object { -not $_.Passed }).Case

    Lists the names of the cases that failed.

    .INPUTS
    None.

    .OUTPUTS
    None, or EliteLab.CheckerCase with -PassThru. The case list and the verdict
    are written to the information stream.

    .LINK
    Start-EliteChecker
    #>
    [CmdletBinding()]
    [OutputType('EliteLab.CheckerCase')]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string] $Id,

        [Parameter(Position = 1)]
        [string] $ScriptPath,

        [ValidateRange(1, 3600)]
        [int] $TimeoutSeconds = 60,

        [switch] $PassThru
    )
    $definition = Resolve-EliteChecker -Id $Id -Cmdlet $PSCmdlet
    if ([string]::IsNullOrEmpty($ScriptPath)) {
        $ScriptPath = (Get-EliteCheckerPath -Definition $definition).Script
    }
    if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
        $message = "There is no script at '{0}'. Set the checker up first:  Start-EliteChecker {1}" -f $ScriptPath, $definition.Id
        $record = New-Object System.Management.Automation.ErrorRecord (
            (New-Object System.IO.FileNotFoundException $message), 'EliteLab.ScriptNotFound',
            [System.Management.Automation.ErrorCategory]::ObjectNotFound, $ScriptPath)
        $PSCmdlet.ThrowTerminatingError($record)
    }
    $ScriptPath = (Resolve-Path -LiteralPath $ScriptPath).ProviderPath

    $cases = @(Get-EliteCheckerCase -Definition $definition)
    $runRoot = Join-Path (Get-EliteTempRoot) ('run-' + [System.Guid]::NewGuid().ToString('N').Substring(0, 12))
    $results = New-Object System.Collections.Generic.List[object]
    try {
        $number = 0
        foreach ($case in $cases) {
            $number++
            $casePath = Join-Path $runRoot ('case-{0:d2}' -f $number)
            $results.Add((Test-EliteCheckerCase -Definition $definition -Case $case -ScriptPath $ScriptPath -CasePath $casePath -TimeoutSeconds $TimeoutSeconds))
        }
    }
    finally {
        if (Test-Path -LiteralPath $runRoot) {
            Remove-Item -LiteralPath $runRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    $failed = @($results | Where-Object { -not $_.Passed })
    Write-EliteLine
    Write-EliteLine ('  {0} - your script against {1} fixture cases' -f $definition.Id, $results.Count)
    Write-EliteLine ('  script: {0}' -f $ScriptPath)
    Write-EliteLine
    foreach ($result in $results) {
        Write-EliteLine ('    [{0}] {1}' -f $result.Verdict, $result.Case)
        if (-not $result.Passed) {
            foreach ($line in (Format-EliteParagraph -Text $result.Detail -Indent '           ')) {
                Write-EliteLine $line
            }
            foreach ($line in (Format-EliteParagraph -Text $result.Why -FirstIndent '           this case: ' -Indent '             ')) {
                Write-EliteLine $line
            }
        }
    }
    Write-EliteLine
    if ($failed.Count -eq 0) {
        Write-EliteLine ('  Verdict: PASS - all {0} cases.' -f $results.Count)
        Write-EliteLine
        foreach ($line in (Format-EliteParagraph -Text $definition.Debrief -Indent '  ')) {
            Write-EliteLine $line
        }
    }
    else {
        Write-EliteLine ('  Verdict: FAIL - {0} of {1} cases failed.' -f $failed.Count, $results.Count)
        Write-EliteLine ('  Fix the script, then run again:  Test-EliteChecker {0}' -f $definition.Id)
    }
    Write-EliteLine

    if ($PassThru) {
        $results.ToArray()
    }
}

#endregion

#region Module set-up

Set-Alias -Name elite -Value Invoke-Elite

Update-TypeData -TypeName 'EliteLab.SetupCheck' -DefaultDisplayPropertySet 'Name', 'Ok', 'Group', 'Detail' -Force
Update-TypeData -TypeName 'EliteLab.Checker' -DefaultDisplayPropertySet 'Id', 'Title', 'Cases' -Force
Update-TypeData -TypeName 'EliteLab.CheckerCase' -DefaultDisplayPropertySet 'Checker', 'Case', 'Verdict', 'Detail' -Force

# elite takes its arguments as $args, so PowerShell has no parameter to hang a completer
# on. A native completer is the one kind that needs none; it is registered for both names.
Register-ArgumentCompleter -Native -CommandName 'elite', 'Invoke-Elite' -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    Get-EliteCommandLineCompletion -WordToComplete ([string]$wordToComplete) -CommandAst $commandAst -CursorPosition $cursorPosition
}

Register-ArgumentCompleter -CommandName 'Get-EliteChecker', 'Start-EliteChecker', 'Test-EliteChecker' -ParameterName 'Id' -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
    $null = $commandName, $parameterName, $commandAst, $fakeBoundParameters   # the signature is PowerShell's
    try {
        foreach ($definition in (Get-EliteCheckerTable).Values) {
            if ($definition.Id.StartsWith([string]$wordToComplete, [System.StringComparison]::OrdinalIgnoreCase)) {
                New-Object System.Management.Automation.CompletionResult $definition.Id, $definition.Id, 'ParameterValue', $definition.Title
            }
        }
    }
    catch {
        Write-Debug "elite: checker completion failed: $_"
    }
}

Export-ModuleMember -Function 'Invoke-Elite', 'Test-EliteSetup', 'Get-EliteChecker', 'Start-EliteChecker', 'Test-EliteChecker' -Alias 'elite'

#endregion
