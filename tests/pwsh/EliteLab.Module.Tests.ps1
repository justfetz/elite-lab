# The module as a whole: what it exports, how it is written, and what it must never do.
# These are the "Robust means" lines of issue #1 that can be checked from the source.

BeforeDiscovery {
    $script:ExportedFunctions = @(
        'Invoke-Elite', 'Test-EliteSetup', 'Get-EliteChecker', 'Start-EliteChecker', 'Test-EliteChecker'
    ) | ForEach-Object { @{ Name = $_ } }

    $moduleFolder = Join-Path (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') 'pwsh') 'EliteLab'
    $script:SourceFiles = @(
        Get-ChildItem -LiteralPath $moduleFolder -Recurse -File |
            Where-Object { $_.Extension -in '.psm1', '.psd1', '.ps1' } |
            ForEach-Object { @{ Name = $_.Name; Path = $_.FullName } }
    )
}

BeforeAll {
    . (Join-Path $PSScriptRoot 'TestHelpers.ps1')
    $script:RepoRoot = Get-TestRepoRoot
    $script:ModuleFolder = Join-Path (Join-Path $script:RepoRoot 'pwsh') 'EliteLab'
    $script:ManifestPath = Join-Path $script:ModuleFolder 'EliteLab.psd1'
    Import-TestModule
}

Describe 'The EliteLab manifest' {
    BeforeAll {
        $script:Manifest = Test-ModuleManifest -Path $script:ManifestPath -ErrorAction Stop
        $script:ManifestData = Import-PowerShellDataFile -Path $script:ManifestPath
    }

    It 'is a valid manifest for a module named EliteLab' {
        $script:Manifest.Name | Should -Be 'EliteLab'
        $script:Manifest.Version | Should -BeOfType ([version])
    }

    It 'supports Windows PowerShell 5.1 and PowerShell 7' {
        $script:ManifestData.PowerShellVersion | Should -Be '5.1'
        $script:ManifestData.CompatiblePSEditions | Should -Contain 'Desktop'
        $script:ManifestData.CompatiblePSEditions | Should -Contain 'Core'
    }

    It 'exports exactly the five functions and the elite alias' {
        $expected = 'Get-EliteChecker', 'Invoke-Elite', 'Start-EliteChecker', 'Test-EliteChecker', 'Test-EliteSetup'
        (@($script:ManifestData.FunctionsToExport) | Sort-Object) -join ',' | Should -Be ($expected -join ',')
        @($script:ManifestData.AliasesToExport) -join ',' | Should -Be 'elite'
        @($script:ManifestData.CmdletsToExport).Count | Should -Be 0
        @($script:ManifestData.VariablesToExport).Count | Should -Be 0
    }
}

Describe 'Import-Module ./pwsh/EliteLab' {
    It 'loads from the clone with no install step' {
        $module = Get-Module -Name EliteLab
        $module | Should -Not -BeNullOrEmpty
        $module.ModuleBase | Should -Be $script:ModuleFolder
    }

    It 'makes the five functions available and nothing private' {
        $names = @(Get-Command -Module EliteLab -CommandType Function | ForEach-Object { $_.Name } | Sort-Object)
        $names -join ',' | Should -Be 'Get-EliteChecker,Invoke-Elite,Start-EliteChecker,Test-EliteChecker,Test-EliteSetup'
    }

    It 'makes elite an alias of Invoke-Elite' {
        $alias = Get-Alias -Name elite
        $alias.Definition | Should -Be 'Invoke-Elite'
        $alias.ModuleName | Should -Be 'EliteLab'
    }

    It 'can be imported again and removed without an error' {
        { Import-TestModule } | Should -Not -Throw
        { Remove-Module -Name EliteLab -Force } | Should -Not -Throw
        Get-Command -Name Invoke-Elite -ErrorAction SilentlyContinue | Should -BeNullOrEmpty
        Import-TestModule
        Get-Command -Name Invoke-Elite | Should -Not -BeNullOrEmpty
    }

    It 'does not change the caller''s $ErrorActionPreference or strict mode' {
        $before = $ErrorActionPreference
        Import-TestModule
        $ErrorActionPreference | Should -Be $before
        # an undefined variable is still allowed out here: strict mode stayed inside the module
        { $null = $thisVariableWasNeverSet } | Should -Not -Throw
    }
}

Describe 'Help for <Name>' -ForEach $script:ExportedFunctions {
    BeforeAll {
        $script:Help = Get-Help -Name $Name -Full
        $script:Command = Get-Command -Name $Name
    }

    It 'has a synopsis of its own' {
        $synopsis = [string]$script:Help.Synopsis
        $synopsis.Trim() | Should -Not -BeNullOrEmpty
        # with no comment-based help, PowerShell prints the syntax as the synopsis
        $synopsis | Should -Not -Match ('^\s*' + [regex]::Escape($Name) + '\s')
    }

    It 'has a description' {
        ($script:Help.Description | Out-String).Trim().Length | Should -BeGreaterThan 40
    }

    It 'has at least one example' {
        @($script:Help.Examples.Example).Count | Should -BeGreaterThan 0
        foreach ($example in @($script:Help.Examples.Example)) {
            ([string]$example.Code).Trim() | Should -Not -BeNullOrEmpty
        }
    }

    It 'describes every parameter it declares' {
        $common = [System.Management.Automation.PSCmdlet]::CommonParameters + [System.Management.Automation.PSCmdlet]::OptionalCommonParameters
        $declared = @($script:Command.Parameters.Keys | Where-Object { $common -notcontains $_ })
        foreach ($parameter in $declared) {
            $text = (Get-Help -Name $Name -Parameter $parameter).Description | Out-String
            $text.Trim() | Should -Not -BeNullOrEmpty -Because "-$parameter of $Name needs a description"
        }
    }
}

Describe 'How the module is written' {
    BeforeAll {
        $script:ModuleFile = Join-Path $script:ModuleFolder 'EliteLab.psm1'
        $tokens = $null
        $errors = $null
        $script:ModuleAst = [System.Management.Automation.Language.Parser]::ParseFile($script:ModuleFile, [ref]$tokens, [ref]$errors)
        $script:ModuleParseErrors = $errors
        $script:Functions = @($script:ModuleAst.FindAll({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true))
    }

    It 'parses without an error' {
        @($script:ModuleParseErrors).Count | Should -Be 0
    }

    It 'turns on strict mode at the top of the module' {
        $statement = $script:ModuleAst.EndBlock.Statements |
            Where-Object { $_.Extent.Text -match '^Set-StrictMode\s+-Version\s+Latest\s*$' }
        $statement | Should -Not -BeNullOrEmpty
    }

    It 'sets $ErrorActionPreference to Stop at the top of the module' {
        $statement = $script:ModuleAst.EndBlock.Statements |
            Where-Object { $_.Extent.Text -match '^\$ErrorActionPreference\s*=\s*''Stop''\s*$' }
        $statement | Should -Not -BeNullOrEmpty
    }

    It 'declares that it needs PowerShell 5.1 or newer' {
        $script:ModuleAst.ScriptRequirements.RequiredPSVersion | Should -Be ([version]'5.1')
    }

    It 'names every function, private ones included, with an approved verb' {
        $approved = @(Get-Verb | ForEach-Object { $_.Verb })
        $script:Functions.Count | Should -BeGreaterThan 20
        foreach ($function in $script:Functions) {
            $function.Name | Should -Match '^[A-Z][a-z]+-Elite[A-Za-z]*$'
            $approved | Should -Contain ($function.Name -split '-')[0] -Because "$($function.Name) must use an approved verb"
        }
    }
}

Describe 'Source file <Name>' -ForEach $script:SourceFiles {
    BeforeAll {
        $tokens = $null
        $errors = $null
        $script:FileAst = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
        $script:FileErrors = $errors
        $script:FileCommands = @($script:FileAst.FindAll({ param($node) $node -is [System.Management.Automation.Language.CommandAst] }, $true) |
                ForEach-Object { $_.GetCommandName() } | Where-Object { $_ } | Sort-Object -Unique)
        $script:FileText = [System.IO.File]::ReadAllText($Path)
    }

    It 'parses without an error' {
        @($script:FileErrors).Count | Should -Be 0
    }

    It 'is plain ASCII, so Windows PowerShell 5.1 reads it the same way PowerShell 7 does' {
        $script:FileText | Should -Not -Match '[^\x00-\x7F]'
    }

    It 'calls commands by their full names, never by an alias' {
        # the alias table of the PowerShell running the test, plus the common ones that
        # exist only on Windows, so the Linux leg catches them too
        $aliases = @(Get-Alias | ForEach-Object { $_.Name }) + @(
            'cat', 'cd', 'cls', 'cp', 'curl', 'diff', 'dir', 'echo', 'kill', 'ls', 'man', 'mv',
            'ps', 'pwd', 'rm', 'rmdir', 'sleep', 'sort', 'tee', 'type', 'wget', 'where', 'write'
        )
        foreach ($command in $script:FileCommands) {
            $aliases | Should -Not -Contain $command -Because "$Name uses the alias '$command'"
        }
    }

    It 'never reaches for the registry, services, accounts, the firewall, the scheduler or the network' {
        $forbidden = @(
            'Set-ItemProperty', 'New-ItemProperty', 'Remove-ItemProperty', 'Get-ItemProperty',
            'New-Service', 'Set-Service', 'Start-Service', 'Stop-Service', 'Restart-Service', 'Remove-Service',
            'Register-ScheduledTask', 'Unregister-ScheduledTask', 'Set-ScheduledTask', 'Start-ScheduledTask',
            'New-LocalUser', 'Set-LocalUser', 'Remove-LocalUser', 'Add-LocalGroupMember', 'Remove-LocalGroupMember',
            'New-NetFirewallRule', 'Set-NetFirewallRule', 'Remove-NetFirewallRule', 'Set-NetFirewallProfile',
            'Invoke-WebRequest', 'Invoke-RestMethod', 'Start-BitsTransfer', 'Test-NetConnection', 'Test-Connection',
            'Set-ExecutionPolicy', 'Start-Process', 'Invoke-Expression', 'Get-WinEvent', 'Get-EventLog',
            'reg', 'reg.exe', 'sc.exe', 'net', 'net.exe', 'netsh', 'schtasks', 'icacls', 'takeown', 'wevtutil'
        )
        foreach ($command in $script:FileCommands) {
            $forbidden | Should -Not -Contain $command -Because "$Name must not call $command"
        }
        # no registry drive, no socket or web client type
        ($script:FileText -replace '(?m)^\s*#.*$', '') | Should -Not -Match '(?i)\b(HKLM|HKCU|HKEY_[A-Z_]+):?\\|\[System\.Net\.|Microsoft\.Win32\.Registry'
    }
}

Describe 'PSScriptAnalyzer' {
    It 'finds nothing in the module, the checkers or these tests with the committed settings' {
        if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) {
            Set-ItResult -Skipped -Because 'PSScriptAnalyzer is not installed here; the CI workflow runs it on every leg'
            return
        }
        # the same runner CI uses: a child process, a time limit, another go if it crashes
        $runner = Join-Path (Join-Path (Join-Path $script:RepoRoot 'tests') 'pwsh') 'Invoke-Analyzer.ps1'
        $findings = @(& $runner -PassThru)
        $report = ($findings | ForEach-Object { '{0}:{1} {2} {3}' -f $_.File, $_.Line, $_.RuleName, $_.Message }) -join "`n"
        $findings.Count | Should -Be 0 -Because $report
    }
}
