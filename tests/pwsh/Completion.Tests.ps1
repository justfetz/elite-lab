# Tab completion for elite: the subcommands, their options and their choices.
# The list is generated from the CLI's own argparse parser (pwsh/build_completions.py).
# These tests fail when the generated file and the parser drift apart.

BeforeDiscovery {
    $dataPath = Join-Path (Join-Path (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') 'pwsh') 'EliteLab') 'EliteLab.Completions.json'
    $tree = Get-Content -LiteralPath $dataPath -Raw | ConvertFrom-Json
    $commandNames = @($tree.commands | ForEach-Object { $_.name })
    $lab = $tree.commands | Where-Object { $_.name -eq 'lab' }
    $learn = $tree.commands | Where-Object { $_.name -eq 'learn' }
    $drill = $tree.commands | Where-Object { $_.name -eq 'drill' }
    $study = $tree.commands | Where-Object { $_.name -eq 'study' }
    $modules = @($learn.positionals[0].choices)

    # the line as typed up to the cursor, and what Tab must offer, in order
    $script:CompletionCases = @(
        @{ Line = 'elite '; Expected = $commandNames }
        @{ Line = 'Invoke-Elite '; Expected = $commandNames }
        @{ Line = 'elite l'; Expected = @($commandNames | Where-Object { $_ -like 'l*' }) }
        @{ Line = 'elite LA'; Expected = @('lab') }
        @{ Line = 'elite doc'; Expected = @('doctor') }
        @{ Line = 'Invoke-Elite dr'; Expected = @('drill') }
        @{ Line = 'elite zz'; Expected = @() }
        @{ Line = 'elite -'; Expected = @('-h', '--help', '--version') }
        @{ Line = 'elite --'; Expected = @('--help', '--version') }
        @{ Line = 'elite --v'; Expected = @('--version') }
        @{ Line = 'elite lab '; Expected = @($lab.commands | ForEach-Object { $_.name }) }
        @{ Line = 'elite lab s'; Expected = @($lab.commands | ForEach-Object { $_.name } | Where-Object { $_ -like 's*' }) }
        @{ Line = 'elite lab --'; Expected = @('--help') }
        @{ Line = 'elite lab start --'; Expected = @('--help') }
        @{ Line = 'elite learn '; Expected = $modules }
        @{ Line = 'elite learn net'; Expected = @('networking') }
        @{ Line = 'elite quiz win'; Expected = @($modules | Where-Object { $_ -like 'win*' }) }
        @{ Line = 'elite tools tools-'; Expected = @($modules | Where-Object { $_ -like 'tools-*' }) }
        @{ Line = 'elite drill '; Expected = @($drill.positionals[0].choices) }
        @{ Line = 'elite study '; Expected = @($study.positionals[0].choices) }
        @{ Line = 'elite engage '; Expected = @('recon') }
        @{ Line = 'elite -h l'; Expected = @($commandNames | Where-Object { $_ -like 'l*' }) }
        @{ Line = 'elite run nmap -'; Expected = @() }
        @{ Line = 'elite run nmap --'; Expected = @() }
        @{ Line = 'elite learn networking -'; Expected = @('-h', '--help') }
        @{ Line = 'elite doctor; elite l'; Expected = @($commandNames | Where-Object { $_ -like 'l*' }) }
    )
}

BeforeAll {
    . (Join-Path $PSScriptRoot 'TestHelpers.ps1')
    $script:RepoRoot = Get-TestRepoRoot
    Import-TestModule

    function Get-Completion {
        # what the real completion engine offers with the cursor at the end of $Line
        param([string] $Line)
        $result = TabExpansion2 -inputScript $Line -cursorColumn $Line.Length
        return , @($result.CompletionMatches | ForEach-Object { $_.CompletionText })
    }
}

Describe 'Tab completion through the PowerShell completion engine' {
    It 'offers the right words for "<Line>"' -ForEach $script:CompletionCases {
        $offered = Get-Completion -Line $Line
        # when elite has nothing to offer, PowerShell falls back to file names; none of
        # those may be mistaken for an elite word, and elite must add nothing of its own
        if ($Expected.Count -eq 0) {
            $known = @((Get-Content -LiteralPath (Join-Path $script:RepoRoot 'pwsh/EliteLab/EliteLab.Completions.json') -Raw | ConvertFrom-Json).commands | ForEach-Object { $_.name })
            foreach ($word in $offered) {
                $known | Should -Not -Contain $word
                $word | Should -Not -BeLike '-*'
            }
            return
        }
        ($offered -join ' ') | Should -BeExactly ($Expected -join ' ')
    }

    It 'completes in the middle of a line, using only the words before the cursor' {
        $line = 'elite lab  wire-01'
        $result = TabExpansion2 -inputScript $line -cursorColumn 10
        $offered = @($result.CompletionMatches | ForEach-Object { $_.CompletionText })
        $offered | Should -Contain 'start'
        $offered | Should -Contain 'submit'
    }

    It 'shows the CLI''s own help text as the tool tip' {
        $result = TabExpansion2 -inputScript 'elite doc' -cursorColumn 9
        $match = @($result.CompletionMatches)[0]
        $match.CompletionText | Should -Be 'doctor'
        $match.ToolTip | Should -Match 'installed'
    }

    It 'completes the -Id of the checker commands' {
        $offered = Get-Completion -Line 'Test-EliteChecker -Id '
        $offered | Should -Contain 'task-audit'
        $offered | Should -Contain 'perm-audit'
        (Get-Completion -Line 'Start-EliteChecker log') | Should -Contain 'logon-burst'
    }
}

Describe 'The completion list and the CLI''s parser' {
    It 'is exactly what the generator produces from the parser today (the drift test)' {
        $python = InModuleScope EliteLab { Get-ElitePython }
        $python.Usable | Should -BeTrue
        $generator = Join-Path (Join-Path $script:RepoRoot 'pwsh') 'build_completions.py'
        $output = & $python.Path $generator --check 2>&1
        $LASTEXITCODE | Should -Be 0 -Because "the completion data is out of date. Run: python pwsh/build_completions.py`n$($output -join "`n")"
    }

    It 'names every subcommand the CLI''s own help lists' {
        $help = @(elite -h) -join "`n"
        $LASTEXITCODE | Should -Be 0
        $help -match '\{([a-z,\-]+)\}' | Should -BeTrue
        $fromHelp = @($Matches[1] -split ',' | Sort-Object)
        $tree = Get-Content -LiteralPath (Join-Path $script:RepoRoot 'pwsh/EliteLab/EliteLab.Completions.json') -Raw | ConvertFrom-Json
        $fromData = @($tree.commands | ForEach-Object { $_.name } | Sort-Object)
        ($fromData -join ',') | Should -BeExactly ($fromHelp -join ',')
    }

    It 'names every mission action the CLI''s own help lists for elite lab' {
        $help = @(elite lab -h) -join "`n"
        $help -match '\{([a-z,\-]+)\}' | Should -BeTrue
        $fromHelp = @($Matches[1] -split ',' | Sort-Object)
        $tree = Get-Content -LiteralPath (Join-Path $script:RepoRoot 'pwsh/EliteLab/EliteLab.Completions.json') -Raw | ConvertFrom-Json
        $lab = $tree.commands | Where-Object { $_.name -eq 'lab' }
        (@($lab.commands | ForEach-Object { $_.name } | Sort-Object) -join ',') | Should -BeExactly ($fromHelp -join ',')
    }

    It 'offers a module that the CLI accepts, and the CLI rejects one that is not offered' {
        $offered = Get-Completion -Line 'elite learn '
        $offered.Count | Should -BeGreaterThan 5
        $null = 'q' | elite learn $offered[0]
        $LASTEXITCODE | Should -Be 0
        $null = elite learn not-a-module 2>$null
        $LASTEXITCODE | Should -Be 2
    }
}

Describe 'Get-EliteCompletion, the function behind the completer' {
    It 'offers nothing after a word that is not a subcommand' {
        $offered = InModuleScope EliteLab { @(Get-EliteCompletion -WordToComplete '' -PrecedingWord @('nonsense')) }
        $offered.Count | Should -Be 0
    }

    It 'offers nothing for a free-text argument' {
        $offered = InModuleScope EliteLab { @(Get-EliteCompletion -WordToComplete '' -PrecedingWord @('lab', 'start')) }
        $offered.Count | Should -Be 0
    }

    It 'offers nothing once another tool''s arguments have begun' {
        $offered = InModuleScope EliteLab { @(Get-EliteCompletion -WordToComplete '-' -PrecedingWord @('run', 'nmap')) }
        $offered.Count | Should -Be 0
    }

    It 'still offers run''s own help option before the tool is named' {
        $offered = InModuleScope EliteLab { @(Get-EliteCompletion -WordToComplete '-' -PrecedingWord @('run')) }
        @($offered | ForEach-Object { $_.CompletionText }) | Should -Contain '--help'
    }

    It 'returns completion results with text, list text and a tool tip' {
        $offered = InModuleScope EliteLab { @(Get-EliteCompletion -WordToComplete 'eng' -PrecedingWord @()) }
        $offered.Count | Should -Be 1
        $offered[0] | Should -BeOfType ([System.Management.Automation.CompletionResult])
        $offered[0].CompletionText | Should -Be 'engage'
        $offered[0].ListItemText | Should -Be 'engage'
        $offered[0].ToolTip | Should -Not -BeNullOrEmpty
    }

    It 'does not throw when the syntax tree is missing' {
        { InModuleScope EliteLab { Get-EliteCommandLineCompletion -WordToComplete 'x' -CommandAst $null -CursorPosition 3 } } | Should -Not -Throw
    }
}
