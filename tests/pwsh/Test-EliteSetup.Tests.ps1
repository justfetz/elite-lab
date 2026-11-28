# Test-EliteSetup: `elite doctor` as objects, one per check.

BeforeAll {
    . (Join-Path $PSScriptRoot 'TestHelpers.ps1')
    Import-TestModule
}

Describe 'Test-EliteSetup on this machine' {
    BeforeAll {
        $script:Checks = @(Test-EliteSetup)
        $script:DoctorLines = @(elite doctor)
        $script:Marked = @($script:DoctorLines | Where-Object { $_ -match '^\s*\[(ok|--|!!)\]\s+\S' })
    }

    It 'returns one object for every check elite doctor prints' {
        $script:Marked.Count | Should -BeGreaterThan 5
        $script:Checks.Count | Should -Be $script:Marked.Count
    }

    It 'returns objects of the type EliteLab.SetupCheck with all seven properties' {
        foreach ($check in $script:Checks) {
            $check.PSObject.TypeNames[0] | Should -Be 'EliteLab.SetupCheck'
            @($check.PSObject.Properties | ForEach-Object { $_.Name }) -join ',' | Should -Be 'Name,Ok,Status,Group,Required,Detail,Install'
            $check.Ok | Should -BeOfType ([bool])
            $check.Required | Should -BeOfType ([bool])
            $check.Name | Should -Not -BeNullOrEmpty
            $check.Status | Should -BeIn 'ok', 'missing', 'problem'
        }
    }

    It 'reports Python first, found and required' {
        $first = $script:Checks[0]
        $first.Name | Should -Be 'Python'
        $first.Ok | Should -BeTrue
        $first.Group | Should -Be 'Core'
        $first.Required | Should -BeTrue
        $first.Detail | Should -Match '^\d+\.\d+ \(good\)$'
    }

    It 'puts every other check in the group elite doctor prints it under, and none of them is required' {
        $others = @($script:Checks | Select-Object -Skip 1)
        @($others | Where-Object { $_.Required }).Count | Should -Be 0
        @($others | ForEach-Object { $_.Group } | Sort-Object -Unique) -join ',' | Should -Be 'Book tutor,External tools'
        @($others | Where-Object { $_.Group -eq 'External tools' }).Count | Should -BeGreaterThan 3
        @($others | Where-Object { $_.Group -eq 'Book tutor' }).Count | Should -BeGreaterThan 1
    }

    It 'agrees with the marks elite doctor printed, line by line' {
        for ($i = 0; $i -lt $script:Marked.Count; $i++) {
            $mark = [regex]::Match($script:Marked[$i], '\[(ok|--|!!)\]').Groups[1].Value
            $script:Checks[$i].Ok | Should -Be ($mark -eq 'ok')
            $script:Marked[$i] | Should -BeLike ('*' + $script:Checks[$i].Name + '*')
        }
    }

    It 'gives the install command for each missing external tool' {
        $missing = @($script:Checks | Where-Object { $_.Group -eq 'External tools' -and -not $_.Ok })
        foreach ($check in $missing) {
            $check.Status | Should -Be 'missing'
            $check.Install | Should -Not -BeNullOrEmpty -Because "$($check.Name) is missing and elite doctor says how to install it"
        }
        foreach ($check in @($script:Checks | Where-Object { $_.Ok })) {
            $check.Install | Should -BeNullOrEmpty
        }
    }

    It 'can be filtered like any other objects' {
        $required = @(Test-EliteSetup | Where-Object { $_.Required -and -not $_.Ok })
        $required.Count | Should -Be 0
    }
}

Describe 'Reading what elite doctor prints' {
    BeforeAll {
        $script:Canned = @(
            ''
            'elite doctor - what''s on this machine'
            ''
            '  [!!] Python 3.7  (need 3.8+)'
            '       The core course runs on Python alone - most missions are playable now.'
            ''
            '  External tools (install only when a mission asks):'
            '    [ok] C compiler (gcc/clang)   for: bin-01 (reverse a crackme), build-04 (fuzz a C target)'
            '    [--] gdb + objdump            for: bin-01 / build-03 when you reverse for real'
            '    [--] nmap                     for: `elite run nmap`, real scanning of your lab'
            ''
            '  For study_books.py (optional local book tutor):'
            '    [ok] pypdf        study_books.py: read PDFs'
            '    [--] sklearn      study_books.py / elite ask: book search (pip install scikit-learn)'
            ''
            '  To install what''s missing (only if you want those missions):'
            '    - gdb + objdump: sudo apt install gdb binutils'
            '    - nmap: sudo apt install nmap   |   macOS: brew install nmap'
            ''
            '  Nothing stopping you from starting:  elite engage'
        )
        $script:Parsed = @(InModuleScope EliteLab -Parameters @{ Lines = $script:Canned } {
                param($Lines)
                ConvertFrom-EliteDoctorOutput -Line $Lines
            })
    }

    It 'finds every marked line and nothing else' {
        ($script:Parsed | ForEach-Object { $_.Name }) -join '|' | Should -Be 'Python|C compiler (gcc/clang)|gdb + objdump|nmap|pypdf|sklearn'
    }

    It 'reads the three marks as ok, missing and problem' {
        ($script:Parsed | ForEach-Object { $_.Status }) -join ',' | Should -Be 'problem,ok,missing,missing,ok,missing'
        ($script:Parsed | ForEach-Object { $_.Ok }) -join ',' | Should -Be 'False,True,False,False,True,False'
    }

    It 'reads the group, the purpose and the install command' {
        $script:Parsed[0].Detail | Should -Be '3.7 (need 3.8+)'
        $script:Parsed[1].Group | Should -Be 'External tools'
        $script:Parsed[1].Detail | Should -Be 'bin-01 (reverse a crackme), build-04 (fuzz a C target)'
        $script:Parsed[2].Install | Should -Be 'sudo apt install gdb binutils'
        $script:Parsed[3].Install | Should -Be 'sudo apt install nmap   |   macOS: brew install nmap'
        $script:Parsed[4].Group | Should -Be 'Book tutor'
        $script:Parsed[5].Detail | Should -Be 'study_books.py / elite ask: book search (pip install scikit-learn)'
        $script:Parsed[5].Install | Should -BeNullOrEmpty
    }

    It 'returns nothing for text that holds no checks' {
        $none = @(InModuleScope EliteLab { ConvertFrom-EliteDoctorOutput -Line @('usage: elite [-h]', '') })
        $none.Count | Should -Be 0
    }
}

Describe 'Test-EliteSetup when elite doctor itself fails' {
    BeforeAll {
        # the stand-in CLI's doctor writes to stderr and exits with 5
        $script:StubClone = Copy-TestClone -Destination (Join-Path $TestDrive 'stub clone') -StubCli
        Import-TestModule -From $script:StubClone
    }

    AfterAll {
        Import-TestModule
    }

    It 'returns one failed check that says what happened, and throws nothing' {
        $ErrorActionPreference = 'Stop'
        { $script:Failed = @(Test-EliteSetup) } | Should -Not -Throw
        $script:Failed.Count | Should -Be 1
        $script:Failed[0].Name | Should -Be 'elite doctor'
        $script:Failed[0].Ok | Should -BeFalse
        $script:Failed[0].Status | Should -Be 'problem'
        $script:Failed[0].Detail | Should -Match 'exited with code 5'
        $script:Failed[0].Detail | Should -Match 'doctor fell over'
    }
}
