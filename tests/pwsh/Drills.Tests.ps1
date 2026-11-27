# The PowerShell command drills in drills/commands.json.
#
# For every drill: the answer parses with the PowerShell parser, uses full cmdlet
# names, and matches its own accept patterns; its one plausible wrong answer parses
# too and is rejected by every pattern. Where the cmdlet exists on the machine running
# the tests (most of them do on the Windows legs), every parameter the answer uses is
# checked against the real cmdlet.
#
# The patterns are regular expressions that the Python CLI runs. They are checked here
# with .NET's engine as well, so a pattern that only one of the two understands fails.

BeforeDiscovery {
    $bankPath = Join-Path (Join-Path (Join-Path (Join-Path $PSScriptRoot '..') '..') 'drills') 'commands.json'
    $bank = Get-Content -LiteralPath $bankPath -Raw | ConvertFrom-Json
    $script:PowerShellDrills = @($bank | Where-Object { $_.platform -eq 'powershell' } | ForEach-Object {
            @{ Id = $_.id; Drill = $_ }
        })

    # other spellings of an answer, and near misses: the same table pytest reads
    $variantPath = Join-Path (Join-Path $PSScriptRoot '..') 'drill_variants.json'
    $script:Variants = @(Get-Content -LiteralPath $variantPath -Raw | ConvertFrom-Json | ForEach-Object { $_ } | ForEach-Object {
            $variant = $_
            @{
                Id       = $variant.id
                Text     = $variant.text
                Accepted = [bool]$variant.accepted
                Verdict  = $(if ($variant.accepted) { 'accepts' } else { 'rejects' })
                Note     = $variant.note
                Drill    = $bank | Where-Object { $_.id -eq $variant.id }
            }
        })
}

BeforeAll {
    . (Join-Path $PSScriptRoot 'TestHelpers.ps1')
    $script:RepoRoot = Get-TestRepoRoot
    $script:Bank = Get-Content -LiteralPath (Join-Path (Join-Path $script:RepoRoot 'drills') 'commands.json') -Raw | ConvertFrom-Json
    $script:Verified = New-Object System.Collections.Generic.List[string]

    function ConvertTo-NormalText {
        # what elitelab.commands._norm does: trim, and collapse runs of whitespace
        param([string] $Text)
        return ($Text.Trim() -replace '\s+', ' ')
    }

    function Test-DrillPattern {
        # true when one of the drill's patterns matches the whole text, ignoring case,
        # which is what re.fullmatch(pattern, text, re.IGNORECASE) does in the CLI
        param($Drill, [string] $Text)
        $options = [System.Text.RegularExpressions.RegexOptions]'IgnoreCase, CultureInvariant'
        $normal = ConvertTo-NormalText -Text $Text
        foreach ($pattern in @($Drill.accept)) {
            $regex = New-Object System.Text.RegularExpressions.Regex ('\A(?:' + $pattern + ')\z'), $options
            if ($regex.IsMatch($normal)) {
                return $true
            }
        }
        return $false
    }

    function Get-ParsedCommand {
        # the syntax tree, the parse errors and the commands of one line of PowerShell
        param([string] $Text)
        $tokens = $null
        $errors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseInput($Text, [ref]$tokens, [ref]$errors)
        $commands = @($ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.CommandAst] }, $true))
        return [pscustomobject]@{ Ast = $ast; Errors = @($errors); Commands = $commands }
    }
}

Describe 'The PowerShell drill bank' {
    It 'adds at least 30 drills for administrators and defenders' {
        @($script:Bank | Where-Object { $_.platform -eq 'powershell' -and $_.id -like 'ps-*' }).Count | Should -BeGreaterOrEqual 30
    }

    It 'covers <Topic>' -ForEach @(
        @{ Topic = 'event logs (Get-WinEvent with filters)'; Pattern = '^Get-WinEvent\b.*-(FilterHashtable|LogName|ListLog|Path)\b' }
        @{ Topic = 'services'; Pattern = '\bGet-Service\b|\bWin32_Service\b' }
        @{ Topic = 'scheduled tasks'; Pattern = '\bGet-ScheduledTask(Info)?\b' }
        @{ Topic = 'local users and groups'; Pattern = '\bGet-Local(User|Group|GroupMember)\b' }
        @{ Topic = 'file permissions (Get-Acl)'; Pattern = '\bGet-Acl\b' }
        @{ Topic = 'firewall rules'; Pattern = '\bGet-NetFirewall(Rule|Profile|PortFilter)\b' }
        @{ Topic = 'file hashes'; Pattern = '\bGet-FileHash\b' }
        @{ Topic = 'processes'; Pattern = '\bGet-Process\b|\bWin32_Process\b' }
        @{ Topic = 'listening ports'; Pattern = '\bGet-Net(TCPConnection|UDPEndpoint)\b' }
        @{ Topic = 'read-only directory queries'; Pattern = '\b(Get-AD\w+|Search-ADAccount)\b' }
    ) {
        $answers = @($script:Bank | Where-Object { $_.platform -eq 'powershell' -and $_.id -like 'ps-*' } | ForEach-Object { $_.answer })
        @($answers | Where-Object { $_ -match $Pattern }).Count | Should -BeGreaterOrEqual 2
    }

    It 'gives every drill a different id' {
        $ids = @($script:Bank | ForEach-Object { $_.id })
        @($ids | Sort-Object -Unique).Count | Should -Be $ids.Count
    }

    It 'only reads: no drill answer uses a verb that changes a machine' {
        $changing = '^(Set|New|Remove|Add|Clear|Stop|Start|Restart|Disable|Enable|Register|Unregister|Invoke|Install|Uninstall|Rename|Move|Copy|Reset|Update|Grant|Revoke)-'
        foreach ($drill in @($script:Bank | Where-Object { $_.platform -eq 'powershell' })) {
            foreach ($command in (Get-ParsedCommand -Text $drill.answer).Commands) {
                $command.GetCommandName() | Should -Not -Match $changing -Because "$($drill.id) must stay a read-only command"
            }
        }
    }

    It 'is stored as plain ASCII' {
        $bytes = [System.IO.File]::ReadAllBytes((Join-Path (Join-Path $script:RepoRoot 'drills') 'commands.json'))
        @($bytes | Where-Object { $_ -gt 127 }).Count | Should -Be 0
    }
}

Describe 'Drill <Id>' -ForEach $script:PowerShellDrills {
    It 'has a prompt, an answer, a reason, patterns and one wrong answer' {
        foreach ($field in 'prompt', 'answer', 'why', 'wrong') {
            [string]$Drill.$field | Should -Not -BeNullOrEmpty -Because "the drill needs '$field'"
        }
        @($Drill.accept).Count | Should -BeGreaterThan 0
    }

    It 'has an answer that parses with the PowerShell parser' {
        $parsed = Get-ParsedCommand -Text $Drill.answer
        ($parsed.Errors | ForEach-Object { $_.Message }) -join '; ' | Should -BeNullOrEmpty
        $parsed.Commands.Count | Should -BeGreaterThan 0
    }

    It 'uses full cmdlet names in its answer, never an alias' {
        foreach ($command in (Get-ParsedCommand -Text $Drill.answer).Commands) {
            $name = $command.GetCommandName()
            $name | Should -Match '^[A-Za-z]+-[A-Za-z0-9]+$'
            $found = Get-Command -Name $name -ErrorAction Ignore | Select-Object -First 1
            if ($null -ne $found) {
                [string]$found.CommandType | Should -Not -Be 'Alias'
            }
        }
    }

    It 'uses only parameters the real cmdlet has (where the cmdlet exists on this machine)' {
        $checkedHere = 0
        foreach ($command in (Get-ParsedCommand -Text $Drill.answer).Commands) {
            $name = $command.GetCommandName()
            $found = $null
            try {
                $found = Get-Command -Name $name -ErrorAction Stop | Select-Object -First 1
            }
            catch {
                $found = $null
            }
            if ($null -eq $found -or $null -eq $found.Parameters -or $found.Parameters.Count -eq 0) {
                continue        # the module is not on this machine (Active Directory, or a Windows-only cmdlet on Linux)
            }
            $valid = @($found.Parameters.Keys) + @($found.Parameters.Values | ForEach-Object { $_.Aliases })
            foreach ($element in $command.CommandElements) {
                if ($element -is [System.Management.Automation.Language.CommandParameterAst]) {
                    $valid | Should -Contain $element.ParameterName -Because "$name has no parameter -$($element.ParameterName)"
                }
            }
            $checkedHere++
            $script:Verified.Add($name)
        }
        if ($checkedHere -eq 0) {
            Set-ItResult -Skipped -Because 'none of its cmdlets are installed on this machine'
        }
    }

    It 'has an answer that matches its own accept patterns' {
        Test-DrillPattern -Drill $Drill -Text $Drill.answer | Should -BeTrue
    }

    It 'still matches when the answer is typed in another case with extra spaces' {
        $sloppy = '  ' + ($Drill.answer.ToUpperInvariant() -replace ' ', '   ') + ' '
        Test-DrillPattern -Drill $Drill -Text $sloppy | Should -BeTrue
    }

    It 'has a wrong answer that parses, differs from the answer and is rejected by every pattern' {
        $parsed = Get-ParsedCommand -Text $Drill.wrong
        ($parsed.Errors | ForEach-Object { $_.Message }) -join '; ' | Should -BeNullOrEmpty
        (ConvertTo-NormalText -Text $Drill.wrong) | Should -Not -Be (ConvertTo-NormalText -Text $Drill.answer)
        Test-DrillPattern -Drill $Drill -Text $Drill.wrong | Should -BeFalse
    }
}

Describe 'Other ways to type the answer to <Id>' -ForEach $script:Variants {
    It '<Verdict> "<Text>" (<Note>)' {
        $Drill | Should -Not -BeNullOrEmpty
        if ($Accepted) {
            # a spelling that is accepted has to be PowerShell that parses
            ((Get-ParsedCommand -Text $Text).Errors | ForEach-Object { $_.Message }) -join '; ' | Should -BeNullOrEmpty
            Test-DrillPattern -Drill $Drill -Text $Text | Should -BeTrue
        }
        else {
            Test-DrillPattern -Drill $Drill -Text $Text | Should -BeFalse
        }
    }
}

Describe 'What the drill checks covered on this machine' {
    It 'reports the cmdlets whose parameters were checked against the real thing' {
        $names = @($script:Verified | Sort-Object -Unique)
        Write-Information -InformationAction Continue -MessageData ('    parameters verified against {0} installed cmdlets: {1}' -f $names.Count, ($names -join ', '))
        $names.Count | Should -BeGreaterThan 3
    }
}
