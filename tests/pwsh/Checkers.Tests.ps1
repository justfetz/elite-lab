# The blue-team checkers: Get-EliteChecker, Start-EliteChecker and Test-EliteChecker.
#
# For every checker: the starter script (nothing solved) fails, a reference solution
# passes every case, and a plausible but wrong solution is caught. Every case is shown
# with its verdict. Everything happens under the temp folder.

BeforeDiscovery {
    $script:CheckerIds = 'baseline-check', 'logon-burst', 'perm-audit', 'task-audit' | ForEach-Object { @{ Id = $_ } }
    $script:OnWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT

    # every wrong solution in tests/pwsh/solutions: <checker>.defective[-<mistake>].ps1
    $script:WrongSolutions = @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'solutions') -Filter '*.defective*.ps1' |
            Sort-Object -Property Name | ForEach-Object {
                @{ Name = $_.Name; Path = $_.FullName; Id = ($_.Name -replace '\.defective.*$', '') }
            })
}

BeforeAll {
    . (Join-Path $PSScriptRoot 'TestHelpers.ps1')
    $script:RepoRoot = Get-TestRepoRoot
    $script:Solutions = Join-Path $PSScriptRoot 'solutions'
    Import-TestModule
    $script:TempRoot = InModuleScope EliteLab { Get-EliteTempRoot }

    function Get-ShownText {
        # everything a command wrote for the learner (the information stream), as lines
        param([scriptblock] $Command)
        return , @(& $Command 6>&1 | ForEach-Object { [string]$_ })
    }

    function Invoke-CheckerRun {
        # one Test-EliteChecker run: the lines it showed and the objects it returned
        param([string] $Id, [string] $ScriptPath, [switch] $NoPassThru)
        $arguments = @{ Id = $Id }
        if ($ScriptPath) {
            $arguments.ScriptPath = $ScriptPath
        }
        if (-not $NoPassThru) {
            $arguments.PassThru = $true
        }
        $all = @(Test-EliteChecker @arguments 6>&1)
        $isShown = { $_ -is [System.Management.Automation.InformationRecord] }
        return @{
            Shown   = @($all | Where-Object $isShown | ForEach-Object { [string]$_ })
            Results = @($all | Where-Object { $_ -isnot [System.Management.Automation.InformationRecord] })
        }
    }

    function Write-TestScript {
        # a learner's script with the given body, in the test drive
        param([string] $Name, [string] $Body)
        $path = Join-Path $TestDrive $Name
        $text = "param([Parameter(Mandatory = `$true)][string] `$Path)`n" + $Body + "`n"
        [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.ASCIIEncoding))
        return $path
    }
}

Describe 'Get-EliteChecker' {
    It 'lists the four checkers the issue asks for' {
        $ids = @(Get-EliteChecker | ForEach-Object { $_.Id } | Sort-Object)
        $ids -join ',' | Should -Be 'baseline-check,logon-burst,perm-audit,task-audit'
    }

    It 'describes each one and gives it at least four fixture cases' {
        foreach ($checker in @(Get-EliteChecker)) {
            $checker.PSObject.TypeNames[0] | Should -Be 'EliteLab.Checker'
            $checker.Title | Should -Not -BeNullOrEmpty
            $checker.Goal | Should -Not -BeNullOrEmpty
            $checker.Cases | Should -BeGreaterOrEqual 4
        }
    }

    It 'returns one checker by id' {
        $checker = @(Get-EliteChecker -Id task-audit)
        $checker.Count | Should -Be 1
        $checker[0].Id | Should -Be 'task-audit'
    }

    It 'keeps every workspace under the temp folder' {
        $script:TempRoot | Should -BeLike ([System.IO.Path]::GetTempPath() + '*')
        foreach ($checker in @(Get-EliteChecker)) {
            $checker.Workspace | Should -BeLike ($script:TempRoot + '*')
            $checker.Script | Should -BeLike ($checker.Workspace + '*')
        }
    }

    It 'gives each user a folder of their own where the temp folder is shared (Linux, macOS)' -Skip:$script:OnWindows {
        (Split-Path -Leaf $script:TempRoot) | Should -Be ('elite-lab-' + [System.Environment]::UserName)
        $null = Get-ShownText { Start-EliteChecker -Id task-audit }
        (Get-Item -LiteralPath $script:TempRoot).UnixMode | Should -Be 'drwx------'
    }

    It 'says which checkers exist when asked for one that does not' {
        { Get-EliteChecker -Id no-such-checker } | Should -Throw -ErrorId 'EliteLab.UnknownChecker*'
        try {
            Get-EliteChecker -Id no-such-checker
        }
        catch {
            $_.Exception.Message | Should -Match "no checker named 'no-such-checker'"
            $_.Exception.Message | Should -Match 'task-audit'
        }
    }
}

Describe 'Checker <Id>' -ForEach $script:CheckerIds {
    BeforeAll {
        $script:Checker = @(Get-EliteChecker -Id $Id)[0]
        $script:Brief = Get-ShownText { Start-EliteChecker -Id $Id -Force }
        $script:Reference = Join-Path $script:Solutions ($Id + '.ps1')
        $script:Defective = Join-Path $script:Solutions ($Id + '.defective.ps1')
    }

    Describe 'Start-EliteChecker' {
        It 'creates the workspace with the brief, a starter script and a sample fixture' {
            $script:Checker.Workspace | Should -Exist
            $script:Checker.Script | Should -Exist
            (Join-Path $script:Checker.Workspace 'START_HERE.txt') | Should -Exist
            @(Get-ChildItem -LiteralPath (Join-Path $script:Checker.Workspace 'sample') -Recurse -File).Count | Should -BeGreaterThan 0
        }

        It 'prints the goal, the rules, where the script is and how to check it' {
            $text = $script:Brief -join "`n"
            $text | Should -Match 'GOAL'
            $text | Should -Match 'THE RULES'
            $text | Should -BeLike ('*' + $script:Checker.Script + '*')
            $text | Should -BeLike ('*Test-EliteChecker ' + $Id + '*')
            (Get-Content -LiteralPath (Join-Path $script:Checker.Workspace 'START_HERE.txt') -Raw) | Should -Match 'THE RULES'
        }

        It 'gives a starter script that parses and declares -Path' {
            $tokens = $null
            $errors = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseFile($script:Checker.Script, [ref]$tokens, [ref]$errors)
            @($errors).Count | Should -Be 0
            @($ast.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath }) | Should -Contain 'Path'
        }

        It 'does not overwrite the learner''s script, unless -Force is given' {
            Add-Content -LiteralPath $script:Checker.Script -Value '# my own work'
            $null = Get-ShownText { Start-EliteChecker -Id $Id }
            (Get-Content -LiteralPath $script:Checker.Script -Raw) | Should -Match '# my own work'
            $null = Get-ShownText { Start-EliteChecker -Id $Id -Force }
            (Get-Content -LiteralPath $script:Checker.Script -Raw) | Should -Not -Match '# my own work'
        }

        It 'writes nothing with -WhatIf' {
            Remove-Item -LiteralPath $script:Checker.Workspace -Recurse -Force
            $null = Get-ShownText { Start-EliteChecker -Id $Id -WhatIf }
            $script:Checker.Workspace | Should -Not -Exist
            $null = Get-ShownText { Start-EliteChecker -Id $Id }
            $script:Checker.Script | Should -Exist
        }
    }

    Describe 'Test-EliteChecker' {
        BeforeAll {
            # one run of each kind, with what was shown and what was returned
            $script:Starter = Invoke-CheckerRun -Id $Id
            $script:Good = Invoke-CheckerRun -Id $Id -ScriptPath $script:Reference
            $script:Bad = Invoke-CheckerRun -Id $Id -ScriptPath $script:Defective
        }

        It 'fails the starter script: an unsolved checker never passes' {
            $script:Starter.Results.Count | Should -Be $script:Checker.Cases
            @($script:Starter.Results | Where-Object { -not $_.Passed }).Count | Should -BeGreaterThan 0
            ($script:Starter.Shown -join "`n") | Should -Match 'Verdict: FAIL'
        }

        It 'passes a correct solution on every case' {
            $script:Good.Results.Count | Should -Be $script:Checker.Cases
            foreach ($result in $script:Good.Results) {
                $result.PSObject.TypeNames[0] | Should -Be 'EliteLab.CheckerCase'
                $result.Passed | Should -BeTrue -Because "case '$($result.Case)': $($result.Detail)"
                $result.Verdict | Should -Be 'pass'
                $result.ExitCode | Should -Be 0
                $result.Checker | Should -Be $Id
            }
        }

        It 'catches a plausible but wrong solution' {
            $failed = @($script:Bad.Results | Where-Object { -not $_.Passed })
            $failed.Count | Should -BeGreaterThan 0
            foreach ($result in $failed) {
                $result.Verdict | Should -Be 'FAIL'
                $result.ExitCode | Should -Be 0 -Because 'the wrong solution runs fine; it is only wrong'
                $result.Detail | Should -Match 'missed|should not be flagged|printed more than once'
                (@($result.Missed).Count + @($result.Unexpected).Count + @($result.Repeated).Count) | Should -BeGreaterThan 0
            }
        }

        It 'shows every case with its verdict, and the overall verdict' {
            foreach ($result in $script:Good.Results) {
                $script:Good.Shown | Should -Contain ('    [pass] ' + $result.Case)
            }
            ($script:Good.Shown -join "`n") | Should -Match ('Verdict: PASS - all ' + $script:Good.Results.Count + ' cases')
        }

        It 'shows what was missed or wrongly flagged, and why the case exists, when a case fails' {
            foreach ($result in $script:Bad.Results) {
                $script:Bad.Shown | Should -Contain ('    [{0}] {1}' -f $result.Verdict, $result.Case)
            }
            $text = $script:Bad.Shown -join "`n"
            $text | Should -Match 'this case:'
            $text | Should -Match ('Verdict: FAIL - \d+ of ' + $script:Bad.Results.Count + ' cases failed')
        }

        It 'returns nothing unless -PassThru is given, and builds the same fixture every time' {
            $again = Invoke-CheckerRun -Id $Id -ScriptPath $script:Reference -NoPassThru
            $again.Results.Count | Should -Be 0
            ($again.Shown -join "`n") | Should -BeExactly ($script:Good.Shown -join "`n")
        }

        It 'removes its fixture folders when it is done' {
            @(Get-ChildItem -LiteralPath $script:TempRoot -Directory -Filter 'run-*').Count | Should -Be 0
        }
    }
}


Describe 'Wrong solution <Name>' -ForEach $script:WrongSolutions {
    # Each of these makes one plausible mistake: it skips a rule, or one spelling of a
    # rule, or a step of the method. A checker that let any of them through would be
    # checking less than its brief says.
    It 'runs without an error and fails at least one case of <Id>' {
        $results = @(Test-EliteChecker -Id $Id -ScriptPath $Path -PassThru 6>$null)
        $results.Count | Should -BeGreaterThan 0
        foreach ($result in $results) {
            $result.ExitCode | Should -Be 0 -Because "the script is only wrong, not broken (case '$($result.Case)': $($result.Detail))"
        }
        $failed = @($results | Where-Object { -not $_.Passed })
        $failed.Count | Should -BeGreaterThan 0 -Because "$Name passed every case of $Id"
        foreach ($result in $failed) {
            $result.Detail | Should -Match 'missed|should not be flagged|printed more than once'
        }
    }
}

Describe 'Test-EliteChecker with scripts that misbehave' {
    It 'fails every case of a script that throws, and says so' {
        $script = Write-TestScript -Name 'throws.ps1' -Body 'throw "this script is broken"'
        $results = @(Test-EliteChecker -Id task-audit -ScriptPath $script -PassThru 6>$null)
        @($results | Where-Object { $_.Passed }).Count | Should -Be 0
        $results[0].Detail | Should -Match 'the script failed \(exit code [1-9]\d*\)'
        $results[0].Detail | Should -Match 'this script is broken'
    }

    It 'fails a script that hits an error it did not handle, even on a case that expects nothing' {
        $script = Write-TestScript -Name 'error.ps1' -Body 'Get-Item -LiteralPath (Join-Path $Path "there-is-no-such-file")'
        $results = @(Test-EliteChecker -Id task-audit -ScriptPath $script -PassThru 6>$null)
        @($results | Where-Object { $_.Passed }).Count | Should -Be 0
    }

    It 'fails a script that calls a command that does not exist' {
        $script = Write-TestScript -Name 'typo.ps1' -Body 'Get-NoSuchCommandAnywhere'
        $results = @(Test-EliteChecker -Id logon-burst -ScriptPath $script -PassThru 6>$null)
        @($results | Where-Object { $_.Passed }).Count | Should -Be 0
    }

    It 'fails a script that exits with a code other than 0' {
        $script = Write-TestScript -Name 'exits.ps1' -Body 'exit 3'
        $results = @(Test-EliteChecker -Id baseline-check -ScriptPath $script -PassThru 6>$null)
        @($results | Where-Object { $_.Passed }).Count | Should -Be 0
        $results[0].ExitCode | Should -Not -Be 0
    }

    It 'stops a script that never ends, and fails it' {
        $script = Write-TestScript -Name 'forever.ps1' -Body 'while ($true) { Start-Sleep -Milliseconds 200 }'
        $timer = [System.Diagnostics.Stopwatch]::StartNew()
        $results = @(Test-EliteChecker -Id task-audit -ScriptPath $script -TimeoutSeconds 2 -PassThru 6>$null)
        $timer.Stop()
        @($results | Where-Object { $_.Passed }).Count | Should -Be 0
        $results[0].Detail | Should -Match 'still running after 2 seconds'
        $timer.Elapsed.TotalSeconds | Should -BeLessThan 90
    }

    It 'fails a script that prints something that is not a finding' {
        # a correct solution, with one line of chatter in front of its findings
        $reference = (Join-Path $script:Solutions 'task-audit.ps1').Replace("'", "''")
        $script = Write-TestScript -Name 'chatty.ps1' -Body ("'Scanning the task list...'`n& '$reference' -Path `$Path")
        $results = @(Test-EliteChecker -Id task-audit -ScriptPath $script -PassThru 6>$null)
        @($results | Where-Object { $_.Passed }).Count | Should -Be 0
        $results[0].Unexpected | Should -Contain 'Scanning the task list...'
    }

    It 'fails a script that prints a finding twice: every brief says once each' {
        $reference = (Join-Path $script:Solutions 'logon-burst.ps1').Replace("'", "''")
        $script = Write-TestScript -Name 'twice.ps1' -Body ("& '$reference' -Path `$Path`n& '$reference' -Path `$Path")
        $results = @(Test-EliteChecker -Id logon-burst -ScriptPath $script -PassThru 6>$null)
        $withFindings = @($results | Where-Object { @($_.Expected).Count -gt 0 })
        $withFindings.Count | Should -BeGreaterThan 0
        foreach ($result in $withFindings) {
            $result.Passed | Should -BeFalse
            $result.Detail | Should -Match 'printed more than once'
            @($result.Repeated).Count | Should -Be @($result.Expected).Count
        }
    }

    It 'accepts a script whose path has a space and an apostrophe in it' {
        $folder = Join-Path $TestDrive "dana's audit scripts"
        $null = New-Item -ItemType Directory -Path $folder -Force
        $script = Join-Path $folder 'find burst.ps1'
        Copy-Item -LiteralPath (Join-Path $script:Solutions 'logon-burst.ps1') -Destination $script
        $results = @(Test-EliteChecker -Id logon-burst -ScriptPath $script -PassThru 6>$null)
        @($results | Where-Object { -not $_.Passed }).Count | Should -Be 0
    }

    It 'does not let the script change this session' {
        $script = Write-TestScript -Name 'meddles.ps1' -Body '$global:EliteLabTestMarker = 1; Set-Location -LiteralPath ([System.IO.Path]::GetTempPath())'
        $here = (Get-Location).Path
        $null = Test-EliteChecker -Id task-audit -ScriptPath $script 6>$null
        (Get-Location).Path | Should -Be $here
        Get-Variable -Name EliteLabTestMarker -Scope Global -ErrorAction Ignore | Should -BeNullOrEmpty
    }

    It 'says where to start when there is no script yet' {
        { Test-EliteChecker -Id task-audit -ScriptPath (Join-Path $TestDrive 'not-written-yet.ps1') } |
            Should -Throw -ErrorId 'EliteLab.ScriptNotFound*'
    }

    It 'says which checkers exist when the id is wrong' {
        { Test-EliteChecker -Id nope } | Should -Throw -ErrorId 'EliteLab.UnknownChecker*'
        { Start-EliteChecker -Id nope } | Should -Throw -ErrorId 'EliteLab.UnknownChecker*'
    }

    It 'says so in plain words when its folder under the temp folder cannot be used' {
        $saved = @{}
        foreach ($name in 'TEMP', 'TMP', 'TMPDIR') {
            $saved[$name] = [System.Environment]::GetEnvironmentVariable($name)
        }
        $blocked = Join-Path $TestDrive 'blocked temp for checkers'
        $null = New-Item -ItemType Directory -Path $blocked -Force
        $reference = Join-Path $script:Solutions 'task-audit.ps1'
        try {
            foreach ($name in 'TEMP', 'TMP', 'TMPDIR') {
                [System.Environment]::SetEnvironmentVariable($name, $blocked)
            }
            # a file sits where the folder should be
            [System.IO.File]::WriteAllText((InModuleScope EliteLab { Get-EliteTempRoot }), 'not a folder')
            { Start-EliteChecker -Id task-audit 6>$null } | Should -Throw -ErrorId 'EliteLab.TempFolderNotUsable*'
            { Test-EliteChecker -Id task-audit -ScriptPath $reference 6>$null } | Should -Throw -ErrorId 'EliteLab.TempFolderNotUsable*'
            try {
                Start-EliteChecker -Id task-audit 6>$null
            }
            catch {
                $_.Exception.Message | Should -Match 'elite cannot write to its folder under the temp folder'
                $_.Exception.Message | Should -Not -Match 'Exception calling'
            }
        }
        finally {
            foreach ($name in 'TEMP', 'TMP', 'TMPDIR') {
                [System.Environment]::SetEnvironmentVariable($name, $saved[$name])
            }
        }
    }
}

Describe 'The checkers and the real system' {
    It 'leaves the clone untouched by a full round of every checker' {
        $before = @(Get-TestFileList -Path $script:RepoRoot)
        foreach ($id in 'baseline-check', 'logon-burst', 'perm-audit', 'task-audit') {
            $null = Get-ShownText { Start-EliteChecker -Id $id -Force }
            $null = Test-EliteChecker -Id $id -ScriptPath (Join-Path $script:Solutions ($id + '.ps1')) 6>$null
        }
        $after = @(Get-TestFileList -Path $script:RepoRoot)
        Compare-Object -ReferenceObject $before -DifferenceObject $after | Should -BeNullOrEmpty
    }

    It 'works for a learner whose temp folder has a non-ASCII name and a space in it' {
        $names = 'TEMP', 'TMP', 'TMPDIR'
        $saved = @{}
        foreach ($name in $names) {
            $saved[$name] = [System.Environment]::GetEnvironmentVariable($name)
        }
        $odd = Join-Path $TestDrive ((Get-TestText -Name UserName) + ' temp')
        $null = New-Item -ItemType Directory -Path $odd -Force
        try {
            foreach ($name in $names) {
                [System.Environment]::SetEnvironmentVariable($name, $odd)
            }
            foreach ($id in 'baseline-check', 'logon-burst', 'perm-audit', 'task-audit') {
                $checker = @(Get-EliteChecker -Id $id)[0]
                $checker.Workspace | Should -BeLike ('*' + (Get-TestText -Name UserName) + ' temp*')
                $null = Get-ShownText { Start-EliteChecker -Id $id -Force }
                $checker.Script | Should -Exist
                $results = @(Test-EliteChecker -Id $id -ScriptPath (Join-Path $script:Solutions ($id + '.ps1')) -PassThru 6>$null)
                foreach ($result in $results) {
                    $result.Passed | Should -BeTrue -Because "$id, case '$($result.Case)': $($result.Detail)"
                }
            }
        }
        finally {
            foreach ($name in $names) {
                [System.Environment]::SetEnvironmentVariable($name, $saved[$name])
            }
        }
    }

    It 'asks for no elevation anywhere in the module or the checkers' {
        $text = ''
        foreach ($file in (Get-ChildItem -LiteralPath (Join-Path $script:RepoRoot 'pwsh/EliteLab') -Recurse -File -Include '*.ps1', '*.psm1')) {
            $text += [System.IO.File]::ReadAllText($file.FullName)
        }
        $text | Should -Not -Match '(?i)#requires\s+-RunAsAdministrator|-Verb\s+RunAs|IsInRole\('
    }
}
