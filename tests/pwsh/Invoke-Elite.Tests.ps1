# Invoke-Elite and its alias, elite: finding Python, handing the arguments over
# unchanged, returning the exit code - and every edge case issue #1 lists:
#
#   a clone path with spaces            a non-ASCII user name
#   no Python on PATH                   Python older than 3.8
#   arguments with quotes and spaces    UTF-8 output
#   the exit code of a failing subcommand

BeforeDiscovery {
    # What the learner types, and exactly what the CLI must receive. The stand-in CLI
    # prints its argument list as JSON, so the comparison is word for word.
    $script:ArgumentCases = @(
        @{ Name = 'no arguments at all'; Call = { elite }; Expected = @() }
        @{ Name = 'plain words'; Call = { elite lab start wire-01 }; Expected = @('lab', 'start', 'wire-01') }
        @{ Name = 'a quoted phrase with spaces'; Call = { elite ask 'what is idor' }; Expected = @('ask', 'what is idor') }
        @{ Name = 'double quotes inside an argument'; Call = { elite ask 'what is "idor"' }; Expected = @('ask', 'what is "idor"') }
        @{ Name = 'a single quote inside an argument'; Call = { elite ask "it's here" }; Expected = @('ask', "it's here") }
        @{ Name = 'two spaces in a row'; Call = { elite ask 'two  spaces' }; Expected = @('ask', 'two  spaces') }
        @{ Name = 'an empty argument'; Call = { elite lab submit wire-01 '' }; Expected = @('lab', 'submit', 'wire-01', '') }
        @{ Name = 'a flag with braces and a colon'; Call = { elite lab submit wire-01 'flag{10.0.0.5:hunter2}' }; Expected = @('lab', 'submit', 'wire-01', 'flag{10.0.0.5:hunter2}') }
        @{ Name = 'a path that ends in a backslash'; Call = { elite run tool 'C:\dir with space\' }; Expected = @('run', 'tool', 'C:\dir with space\') }
        @{ Name = 'backslashes before a double quote'; Call = { elite ask 'a\\"b\' }; Expected = @('ask', 'a\\"b\') }
        @{ Name = 'characters cmd.exe treats as special'; Call = { elite ask '100% & | < > ^ !' }; Expected = @('ask', '100% & | < > ^ !') }
        @{ Name = 'a tab and a new line'; Call = { elite ask "tab`there`nnext" }; Expected = @('ask', "tab`there`nnext") }
        @{ Name = 'the short help option'; Call = { elite -h }; Expected = @('-h') }
        @{ Name = 'a long option'; Call = { elite --version }; Expected = @('--version') }
        @{ Name = 'an option after a subcommand'; Call = { elite lab -h }; Expected = @('lab', '-h') }
        @{ Name = 'another tool''s options, in order'; Call = { elite run nmap -sV -p 80 10.0.0.5 -oN out.txt }; Expected = @('run', 'nmap', '-sV', '-p', '80', '10.0.0.5', '-oN', 'out.txt') }
        @{ Name = 'a comma list (PowerShell makes it an array)'; Call = { elite run nmap -p 80,443 10.0.0.5 }; Expected = @('run', 'nmap', '-p', '80,443', '10.0.0.5') }
        @{ Name = 'an option joined to its value by a colon'; Call = { elite run tool -o:x -mc:200 }; Expected = @('run', 'tool', '-o:x', '-mc:200') }
        @{ Name = 'a quoted option that ends in a colon stays its own word'; Call = { elite run tool '-o:' x }; Expected = @('run', 'tool', '-o:', 'x') }
        @{ Name = 'an option with a file name in it (PowerShell splits it at the dot)'; Call = { elite run john -w=rockyou.txt hashes.txt }; Expected = @('run', 'john', '-w=rockyou.txt', 'hashes.txt') }
        @{ Name = 'an option with an address in it'; Call = { elite run nmap -S10.0.0.5 -T4 10.0.0.9 }; Expected = @('run', 'nmap', '-S10.0.0.5', '-T4', '10.0.0.9') }
        @{ Name = 'an option with a dotted name and a decimal'; Call = { elite run tool -Dkey.name=1 -t1.5 }; Expected = @('run', 'tool', '-Dkey.name=1', '-t1.5') }
        @{ Name = 'an option followed by a word that starts with a dot stays two words'; Call = { elite run tool -w ./words.txt -x .php -C .. }; Expected = @('run', 'tool', '-w', './words.txt', '-x', '.php', '-C', '..') }
        @{ Name = 'a wildcard and a tilde, as typed'; Call = { elite run tool *.md ~/notes.txt }; Expected = @('run', 'tool', '*.md', '~/notes.txt') }
        @{ Name = 'a quoted help switch'; Call = { elite run curl '-?' }; Expected = @('run', 'curl', '-?') }
        @{ Name = 'a quoted comma list of numbers keeps its text'; Call = { elite run tool '0x10,007' }; Expected = @('run', 'tool', '0x10,007') }
        @{ Name = 'numbers keep the text that was typed'; Call = { elite run tool 0x10 1.0 007 1e3 -5 }; Expected = @('run', 'tool', '0x10', '1.0', '007', '1e3', '-5') }
        @{ Name = 'a quoted double dash'; Call = { elite run nmap '--' -x }; Expected = @('run', 'nmap', '--', '-x') }
        @{ Name = 'a URL with a query string'; Call = { elite run sqlmap -u 'http://10.0.0.5/item?id=1' --batch }; Expected = @('run', 'sqlmap', '-u', 'http://10.0.0.5/item?id=1', '--batch') }
        @{ Name = 'a splatted list'; Call = { $list = 'ask', 'a b', '-c'; elite @list }; Expected = @('ask', 'a b', '-c') }
        @{ Name = 'a variable that holds nothing is dropped'; Call = { $nothing = $null; elite ask $nothing done }; Expected = @('ask', 'done') }
        @{ Name = 'a variable that holds an empty list is dropped'; Call = { $none = @(); elite ask $none done }; Expected = @('ask', 'done') }
    )

    $script:OldPythons = @(
        @{ Printed = '3 7 17'; Shown = '3.7.17' }
        @{ Printed = '3 6 9'; Shown = '3.6.9' }
        @{ Printed = '(2, 7, 18)'; Shown = '2.7.18' }
    )
}

BeforeAll {
    . (Join-Path $PSScriptRoot 'TestHelpers.ps1')
    $script:RepoRoot = Get-TestRepoRoot
    $script:OriginalPath = $env:PATH

    # a stand-in CLI inside a clone whose path has a space in it
    $script:StubClone = Copy-TestClone -Destination (Join-Path $TestDrive 'elite lab clone') -StubCli
    # the real CLI inside a clone whose path has spaces
    $script:RealClone = Copy-TestClone -Destination (Join-Path $TestDrive 'real clone with spaces')

    function Get-StubArgument {
        # the argument list the stand-in CLI reports, from the JSON line it prints
        param([object[]] $Output)
        $line = @($Output | ForEach-Object { [string]$_ } | Where-Object { $_ -like '{"argv":*' }) | Select-Object -Last 1
        if ($null -eq $line) {
            throw "the stand-in CLI printed no argument list. It printed: $($Output -join ' | ')"
        }
        return , @((ConvertFrom-Json -InputObject $line).argv)
    }
}

AfterAll {
    $env:PATH = $script:OriginalPath
    Import-TestModule
}

Describe 'elite runs the real CLI' {
    BeforeAll {
        Import-TestModule
    }

    It 'prints what the CLI prints and nothing else' {
        $output = @(elite --version)
        $output.Count | Should -Be 1
        $output[0] | Should -BeOfType ([string])
        $output[0] | Should -Match '^elite-lab \d+\.\d+\.\d+$'
        $LASTEXITCODE | Should -Be 0
    }

    It 'works under its full name, Invoke-Elite' {
        @(Invoke-Elite --version)[0] | Should -Match '^elite-lab '
    }

    It 'runs elite doctor (the "done when" line of the issue)' {
        $output = @(elite doctor)
        $LASTEXITCODE | Should -Be 0
        ($output -join "`n") | Should -Match 'elite doctor'
        ($output -join "`n") | Should -Match '\[ok\] Python \d+\.\d+'
    }

    It 'leaves the exit code of a failing subcommand in $LASTEXITCODE' {
        $null = elite learn no-such-module 2>$null
        $LASTEXITCODE | Should -Be 2
    }

    It 'keeps that exit code when the caller merges stderr into the output' {
        # Windows PowerShell 5.1 turns a native program's redirected stderr into error
        # records; under 'Stop' that would be an exception instead of an exit code.
        $ErrorActionPreference = 'Stop'
        { $script:Merged = @(elite learn no-such-module 2>&1) } | Should -Not -Throw
        $LASTEXITCODE | Should -Be 2
        (($script:Merged | ForEach-Object { [string]$_ }) -join "`n") | Should -Match 'invalid choice'
    }

    It 'gives piped text to the CLI as its input' {
        $output = @('q' | elite learn networking)
        $LASTEXITCODE | Should -Be 0
        ($output -join "`n") | Should -Match 'lesson 1/'
        # the q was understood: the CLI stopped instead of going on to the next lesson
        ($output -join "`n") | Should -Not -Match 'lesson 2/'
    }

    It 'prints UTF-8 text from the real CLI intact when it is captured' {
        $line = @(elite path) | Where-Object { $_ -like 'Lakefront Paper*' } | Select-Object -First 1
        $line | Should -Not -BeNullOrEmpty
        $line | Should -BeLike ('Lakefront Paper {0} your campaign*' -f (Get-TestText -Name EmDash))
    }

    It 'leaves the environment and the console encoding as it found them' {
        $codePage = [System.Console]::OutputEncoding.CodePage
        $saved = @{ PYTHONUTF8 = $env:PYTHONUTF8; PYTHONIOENCODING = $env:PYTHONIOENCODING }
        $env:PYTHONUTF8 = 'the-learners-own-value'
        $env:PYTHONIOENCODING = 'latin-1'
        try {
            $null = elite --version
            $LASTEXITCODE | Should -Be 0
            $env:PYTHONUTF8 | Should -Be 'the-learners-own-value'
            $env:PYTHONIOENCODING | Should -Be 'latin-1'
        }
        finally {
            $env:PYTHONUTF8 = $saved.PYTHONUTF8
            $env:PYTHONIOENCODING = $saved.PYTHONIOENCODING
        }
        $env:ELITELAB_ARGV | Should -BeNullOrEmpty
        [System.Console]::OutputEncoding.CodePage | Should -Be $codePage
    }
}

Describe 'elite from a clone path with spaces' {
    BeforeAll {
        Import-TestModule -From $script:RealClone
    }

    AfterAll {
        Import-TestModule
    }

    It 'is loaded from the path with spaces' {
        (Get-Module -Name EliteLab).ModuleBase | Should -BeLike '*real clone with spaces*'
    }

    It 'runs elite doctor' {
        $output = @(elite doctor)
        $LASTEXITCODE | Should -Be 0
        ($output -join "`n") | Should -Match '\[ok\] Python'
    }

    It 'runs a command that reads the clone''s own data files' {
        $output = @(elite list)
        $LASTEXITCODE | Should -Be 0
        ($output -join "`n") | Should -Match 'networking'
    }
}

Describe 'elite for a learner with a non-ASCII user name' {
    # The user name is in the home folder, the temp folder and, usually, the clone's path.
    BeforeAll {
        $script:UserHome = Join-Path $TestDrive (Get-TestText -Name UserName)
        $script:UserClone = Copy-TestClone -Destination (Join-Path $script:UserHome 'elite-lab')
        $script:SavedHome = @{ HOME = $env:HOME; USERPROFILE = $env:USERPROFILE }
        $env:HOME = $script:UserHome
        $env:USERPROFILE = $script:UserHome
        Import-TestModule -From $script:UserClone
    }

    AfterAll {
        $env:HOME = $script:SavedHome.HOME
        $env:USERPROFILE = $script:SavedHome.USERPROFILE
        Import-TestModule
    }

    It 'runs from a clone under that name' {
        $output = @(elite --version)
        $LASTEXITCODE | Should -Be 0
        $output[0] | Should -Match '^elite-lab '
    }

    It 'writes the progress file under that home folder, and reads it back' {
        $null = elite lab hint wire-01
        $LASTEXITCODE | Should -Be 0
        $progress = Join-Path $script:UserHome '.elite_lab_progress.json'
        $progress | Should -Exist
        $state = Get-Content -LiteralPath $progress -Raw | ConvertFrom-Json
        $state.labs.'wire-01'.hints | Should -Be 1
        $status = @(elite lab status) -join "`n"
        $status | Should -Match 'wire-01\s+.*hints used 1/'
    }
}

Describe 'elite hands every argument to the CLI unchanged' {
    BeforeAll {
        Import-TestModule -From $script:StubClone
    }

    AfterAll {
        Import-TestModule
    }

    It 'passes <Name>' -ForEach $script:ArgumentCases {
        $received = Get-StubArgument -Output @(& $Call)
        $LASTEXITCODE | Should -Be 0
        $received.Count | Should -Be $Expected.Count
        for ($i = 0; $i -lt $Expected.Count; $i++) {
            $received[$i] | Should -BeExactly $Expected[$i]
        }
    }

    It 'passes non-ASCII text' {
        $text = Get-TestText -Name Sentence
        $received = Get-StubArgument -Output @(elite ask $text)
        $received.Count | Should -Be 2
        $received[1] | Should -BeExactly $text
    }

    It 'passes a long argument' {
        $long = 'x' * 6000
        $received = Get-StubArgument -Output @(elite ask $long)
        $received[1] | Should -BeExactly $long
    }

    It 'prints UTF-8 text intact when the output is captured' {
        $output = @(elite --utf8)
        $output[0] | Should -BeExactly (Get-TestText -Name Sentence)
    }

    It 'gives piped lines to the CLI as its input, non-ASCII included' {
        $word = 'caf{0}' -f [char]0x00E9
        $output = @('alpha', $word, '' | elite --stdin)
        $LASTEXITCODE | Should -Be 0
        $line = $output | Where-Object { $_ -like 'stdin=*' } | Select-Object -First 1
        $received = ConvertFrom-Json -InputObject ($line.Substring(6))
        # exactly these lines: no byte-order mark in front, no carriage returns, no '?'
        $received | Should -BeExactly ("alpha`n{0}`n`n" -f $word)
    }

    It 'gives the CLI an empty input, not the keyboard, when nothing is piped in' {
        $output = @(@() | elite --stdin)
        ($output | Where-Object { $_ -like 'stdin=*' } | Select-Object -First 1) | Should -BeExactly 'stdin=""'
    }

    It 'removes the file it used to hand the piped text over' {
        $null = 'one', 'two' | elite --stdin
        $root = InModuleScope EliteLab { Get-EliteTempRoot }
        $root | Should -Exist
        @(Get-ChildItem -LiteralPath $root -Filter 'input-*.txt').Count | Should -Be 0
        $env:ELITELAB_STDIN | Should -BeNullOrEmpty
    }

    It 'says so in plain words, and does not start the CLI, when it cannot write the piped text down' {
        # the module's folder under the temp folder is taken by a file of the same name
        $saved = @{}
        foreach ($name in 'TEMP', 'TMP', 'TMPDIR') {
            $saved[$name] = [System.Environment]::GetEnvironmentVariable($name)
        }
        $blocked = Join-Path $TestDrive 'blocked temp'
        $null = New-Item -ItemType Directory -Path $blocked -Force
        try {
            foreach ($name in 'TEMP', 'TMP', 'TMPDIR') {
                [System.Environment]::SetEnvironmentVariable($name, $blocked)
            }
            $root = InModuleScope EliteLab { Get-EliteTempRoot }
            $root | Should -BeLike ($blocked + '*')
            [System.IO.File]::WriteAllText($root, 'not a folder')
            { $script:Message = Get-TestShownText { 'q' | elite --stdin } } | Should -Not -Throw
            $script:Message | Should -Match 'elite cannot write to its folder under the temp folder'
            $script:Message | Should -Match 'Point TMPDIR \(TEMP on Windows\) at a folder of your own'
            $script:Message | Should -Not -Match 'stdin='
            $LASTEXITCODE | Should -Be 1
        }
        finally {
            foreach ($name in 'TEMP', 'TMP', 'TMPDIR') {
                [System.Environment]::SetEnvironmentVariable($name, $saved[$name])
            }
        }
    }

    It 'returns exit code <_> from the CLI' -ForEach 0, 1, 2, 7, 42 {
        $null = elite --exit $_
        $LASTEXITCODE | Should -Be $_
    }

    It 'keeps the exit code and both streams of a CLI that fails while writing to stderr' {
        $ErrorActionPreference = 'Stop'
        { $script:Merged = @(elite --stderr-then-exit 3 2>&1) } | Should -Not -Throw
        $LASTEXITCODE | Should -Be 3
        $text = ($script:Merged | ForEach-Object { [string]$_ }) -join "`n"
        $text | Should -Match 'this went to stdout'
        $text | Should -Match 'this went to stderr'
    }

    It 'is not turned into an exception by $PSNativeCommandUseErrorActionPreference' {
        $ErrorActionPreference = 'Stop'
        $PSNativeCommandUseErrorActionPreference = $true
        { $null = elite --exit 9 } | Should -Not -Throw
        $LASTEXITCODE | Should -Be 9
        $PSNativeCommandUseErrorActionPreference | Should -BeTrue
    }

    It 'tells Python to use UTF-8 and removes its own variable before the CLI starts work' {
        $line = @(elite --env PYTHONUTF8 PYTHONIOENCODING ELITELAB_ARGV) | Select-Object -Last 1
        $seen = ConvertFrom-Json -InputObject $line
        $seen.PYTHONUTF8 | Should -Be '1'
        $seen.PYTHONIOENCODING | Should -Be 'utf-8'
        $seen.ELITELAB_ARGV | Should -BeNullOrEmpty
    }
}

Describe 'elite when Python is missing' {
    BeforeAll {
        Import-TestModule
        $script:EmptyFolder = Join-Path $TestDrive 'no python here'
        $null = New-Item -ItemType Directory -Path $script:EmptyFolder -Force
    }

    BeforeEach {
        $env:PATH = $script:EmptyFolder
    }

    AfterEach {
        $env:PATH = $script:OriginalPath
    }

    It 'says so in plain words, with the install command, and throws nothing' {
        $errorsBefore = $Error.Count
        { $script:Message = Get-TestShownText { elite doctor } } | Should -Not -Throw
        $shown = $script:Message
        $shown | Should -Match 'elite needs Python 3\.8 or newer, and none was found on your PATH'
        $shown | Should -Match 'Install it:\s+\S'
        if (Test-OnWindows) {
            $shown | Should -Match 'winget install --exact --id Python\.Python\.3'
        }
        else {
            $shown | Should -Match '(apt|brew) install python'
        }
        $shown | Should -Not -Match '(?i)exception|at line|CategoryInfo|FullyQualifiedErrorId|Traceback'
        $Error.Count | Should -Be $errorsBefore
    }

    It 'sets the exit code to 127' {
        $global:LASTEXITCODE = 0
        $null = elite doctor 6>&1
        $LASTEXITCODE | Should -Be 127
    }

    It 'writes nothing to the output stream, so a script cannot mistake the message for data' {
        $output = @(elite doctor 6>$null)
        $output.Count | Should -Be 0
    }

    It 'makes Test-EliteSetup return one failed Python check instead of throwing' {
        $checks = @(Test-EliteSetup)
        $checks.Count | Should -Be 1
        $checks[0].Name | Should -Be 'Python'
        $checks[0].Ok | Should -BeFalse
        $checks[0].Status | Should -Be 'missing'
        $checks[0].Required | Should -BeTrue
        $checks[0].Install | Should -Match 'install'
    }
}

Describe 'elite when Python is older than 3.8' {
    BeforeAll {
        Import-TestModule
    }

    AfterEach {
        $env:PATH = $script:OriginalPath
    }

    It 'names the version it found (<Shown>) and prints the install command' -ForEach $script:OldPythons {
        $folder = Join-Path $TestDrive ('old python ' + $Shown)
        $null = Write-FakePython -Directory $folder -Name 'python3' -Output $Printed
        $null = Write-FakePython -Directory $folder -Name 'python' -Output $Printed
        $env:PATH = $folder

        { $script:Message = Get-TestShownText { elite doctor } } | Should -Not -Throw
        $script:Message | Should -Match 'elite needs Python 3\.8 or newer'
        $script:Message | Should -Match ('The newest one found is Python ' + [regex]::Escape($Shown))
        $script:Message | Should -Match 'Install it:\s+\S'
        $LASTEXITCODE | Should -Be 127

        $checks = @(Test-EliteSetup)
        $checks.Count | Should -Be 1
        $checks[0].Ok | Should -BeFalse
        $checks[0].Status | Should -Be 'problem'
        $checks[0].Detail | Should -Match ([regex]::Escape($Shown))
    }

    It 'says a Python that does not start was found but did not run' {
        $folder = Join-Path $TestDrive 'broken python'
        $null = Write-FakePython -Directory $folder -Name 'python' -ExitCode 9
        $env:PATH = $folder
        $shown = Get-TestShownText { elite doctor }
        $shown | Should -Match 'was found at .+ but it did not run'
        $LASTEXITCODE | Should -Be 127
    }
}

Describe 'How elite chooses a Python' {
    BeforeAll {
        Import-TestModule
    }

    AfterEach {
        $env:PATH = $script:OriginalPath
    }

    It 'prefers the py launcher, then python3, then python' {
        $folder = Join-Path $TestDrive 'three pythons'
        $null = Write-FakePython -Directory $folder -Name 'py' -Output '3 12 1'
        $null = Write-FakePython -Directory $folder -Name 'python3' -Output '3 11 2'
        $null = Write-FakePython -Directory $folder -Name 'python' -Output '3 10 0'
        $env:PATH = $folder
        $chosen = InModuleScope EliteLab { Get-ElitePython }
        $chosen.Usable | Should -BeTrue
        $chosen.Name | Should -Be 'py'
        $chosen.Version | Should -Be ([version]'3.12.1')
    }

    It 'falls back to python3 when there is no launcher' {
        $folder = Join-Path $TestDrive 'two pythons'
        $null = Write-FakePython -Directory $folder -Name 'python3' -Output '3 11 2'
        $null = Write-FakePython -Directory $folder -Name 'python' -Output '3 10 0'
        $env:PATH = $folder
        (InModuleScope EliteLab { Get-ElitePython }).Name | Should -Be 'python3'
    }

    It 'skips a launcher that is too old and uses the next Python that is new enough' {
        $folder = Join-Path $TestDrive 'old launcher'
        $null = Write-FakePython -Directory $folder -Name 'py' -Output '3 6 9'
        $null = Write-FakePython -Directory $folder -Name 'python' -Output '3 9 4'
        $env:PATH = $folder
        $chosen = InModuleScope EliteLab { Get-ElitePython }
        $chosen.Usable | Should -BeTrue
        $chosen.Name | Should -Be 'python'
    }

    It 'accepts a Python that prints <Printed>: 3.8.0 is enough, and 3.10 is newer than 3.8' -ForEach @(
        @{ Printed = '3 8 0' }
        @{ Printed = '3 10 2' }
        @{ Printed = '3 14 0' }
    ) {
        $folder = Join-Path $TestDrive ('edge ' + $Printed)
        $null = Write-FakePython -Directory $folder -Name 'python3' -Output $Printed
        $env:PATH = $folder
        (InModuleScope EliteLab { Get-ElitePython }).Usable | Should -BeTrue
    }

    It 'looks again when PATH changes' {
        $folder = Join-Path $TestDrive 'path one'
        $null = Write-FakePython -Directory $folder -Name 'python3' -Output '3 6 9'
        $env:PATH = $folder
        (InModuleScope EliteLab { Get-ElitePython }).Usable | Should -BeFalse
        $env:PATH = $script:OriginalPath
        (InModuleScope EliteLab { Get-ElitePython }).Usable | Should -BeTrue
    }
}
