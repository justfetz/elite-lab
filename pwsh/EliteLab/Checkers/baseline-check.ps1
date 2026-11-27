# Checker: report which settings in a fixture configuration miss a stated baseline.
#
# The fixture is two JSON files: the baseline and an exported configuration. Nothing
# here reads the registry, a policy or any real setting. Every case is the compliant
# configuration with a few values changed (Change) or left out (Omit).

@{
    Id         = 'baseline-check'
    Title      = 'Report the settings that miss the baseline'
    Goal       = 'Compare an exported configuration with a stated baseline and print the name of every setting that misses it.'
    ScriptName = 'Test-Baseline.ps1'

    Brief      = @(
        'The fixture is two files:'
        '  baseline.json  the rules. Each has a name, a rule and a value. The rule is'
        '                 atLeast (the setting must be that number or more), atMost (that'
        '                 number or less) or equals (exactly that value).'
        '  settings.json  what the machine is set to: one object, one property per setting.'
        ''
        'A setting misses the baseline when it breaks any rule that names it, or when it'
        'is not in settings.json at all. A setting the baseline does not name is fine.'
        'Exports are sloppy: a number can arrive as text ("9"). Compare numbers as numbers.'
        ''
        'Print the name of every setting that misses the baseline, once each.'
    )

    Starter    = @'
<#
Test-Baseline.ps1 - report which settings miss the stated baseline.
The rules are in START_HERE.txt, next to this file.
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$baseline = Get-Content -LiteralPath (Join-Path $Path 'baseline.json') -Raw | ConvertFrom-Json
$settings = Get-Content -LiteralPath (Join-Path $Path 'settings.json') -Raw | ConvertFrom-Json

# TODO: print the name of every setting that misses the baseline, one per line.
# One property of $settings by name:  $settings.PSObject.Properties[$rule.name]
foreach ($rule in $baseline) {
}
'@

    Debrief    = 'A baseline is only useful if something checks it. The traps here are the real ones: a missing setting that reads as compliant, a number that arrives as text, a value such as 0 that satisfies one limit and means "off". On a real machine the left-hand side comes from secedit /export, Get-ItemProperty or a CIS or Microsoft security baseline; the comparison is the same.'

    Baseline   = @(
        @{ Name = 'MinimumPasswordLength'; Rule = 'atLeast'; Value = 14 }
        @{ Name = 'MaximumPasswordAgeDays'; Rule = 'atMost'; Value = 365 }
        @{ Name = 'LockoutThreshold'; Rule = 'atLeast'; Value = 1 }
        @{ Name = 'LockoutThreshold'; Rule = 'atMost'; Value = 5 }
        @{ Name = 'LockoutDurationMinutes'; Rule = 'atLeast'; Value = 15 }
        @{ Name = 'PasswordComplexity'; Rule = 'equals'; Value = $true }
        @{ Name = 'Smb1Enabled'; Rule = 'equals'; Value = $false }
        @{ Name = 'GuestAccountEnabled'; Rule = 'equals'; Value = $false }
        @{ Name = 'RdpNetworkLevelAuth'; Rule = 'equals'; Value = $true }
        @{ Name = 'FirewallDomainProfile'; Rule = 'equals'; Value = 'On' }
        @{ Name = 'AuditLogonFailures'; Rule = 'equals'; Value = $true }
    )

    # every value on its limit or better; the last two are not in the baseline
    Compliant  = [ordered]@{
        MinimumPasswordLength  = 14
        MaximumPasswordAgeDays = 365
        LockoutThreshold       = 5
        LockoutDurationMinutes = 15
        PasswordComplexity     = $true
        Smb1Enabled            = $false
        GuestAccountEnabled    = $false
        RdpNetworkLevelAuth    = $true
        FirewallDomainProfile  = 'On'
        AuditLogonFailures     = $true
        ScreenLockSeconds      = 900
        HostName               = 'ws01'
    }

    Build      = {
        param($CasePath, $Case, $Definition)
        $settings = [ordered]@{}
        foreach ($name in $Definition.Compliant.Keys) {
            $settings[$name] = $Definition.Compliant[$name]
        }
        if ($Case.ContainsKey('Change')) {
            foreach ($name in $Case.Change.Keys) {
                $settings[$name] = $Case.Change[$name]
            }
        }
        if ($Case.ContainsKey('Omit')) {
            foreach ($name in @($Case.Omit)) {
                $settings.Remove($name)
            }
        }
        $rules = @($Definition.Baseline | ForEach-Object {
                [pscustomobject][ordered]@{ name = $_.Name; rule = $_.Rule; value = $_.Value }
            })
        Write-EliteTextFile -Path (Join-Path $CasePath 'baseline.json') -Text ((ConvertTo-Json -InputObject $rules -Depth 3) + "`n")
        Write-EliteTextFile -Path (Join-Path $CasePath 'settings.json') -Text ((ConvertTo-Json -InputObject ([pscustomobject]$settings) -Depth 3) + "`n")
    }

    Sample     = @{
        Name   = 'sample'
        Change = @{ MinimumPasswordLength = 10; Smb1Enabled = $true }
        Omit   = @('AuditLogonFailures')
    }

    Cases      = @(
        @{
            Name     = 'everything meets the baseline'
            Why      = 'Every value is on its limit or better: 14 is at least 14, 365 is at most 365, and false equals false. Two settings are not in the baseline at all.'
            Expected = @()
        }
        @{
            Name     = 'numbers on the wrong side'
            Why      = 'A password length of 8, a password age of 400 days and a lockout of 5 minutes: three numeric rules broken, one of each direction.'
            Change   = @{ MinimumPasswordLength = 8; MaximumPasswordAgeDays = 400; LockoutDurationMinutes = 5 }
            Expected = @('MinimumPasswordLength', 'MaximumPasswordAgeDays', 'LockoutDurationMinutes')
        }
        @{
            Name     = 'switches set the wrong way'
            Why      = 'SMB1 is on, password complexity is off and the firewall profile is "Off". GuestAccountEnabled is false, which is what the baseline asks for: a script that treats false as a miss flags it wrongly.'
            Change   = @{ Smb1Enabled = $true; PasswordComplexity = $false; FirewallDomainProfile = 'Off' }
            Expected = @('Smb1Enabled', 'PasswordComplexity', 'FirewallDomainProfile')
        }
        @{
            Name     = 'settings that are missing'
            Why      = 'Three settings are not in the export. A setting that is absent cannot meet its baseline, and in PowerShell $null -le 365 is true: loop over the baseline, not over the settings.'
            Omit     = @('MaximumPasswordAgeDays', 'GuestAccountEnabled', 'AuditLogonFailures')
            Expected = @('MaximumPasswordAgeDays', 'GuestAccountEnabled', 'AuditLogonFailures')
        }
        @{
            Name     = 'two rules for one setting: below the lower one'
            Why      = 'LockoutThreshold is 0: it passes "at most 5" and fails "at least 1", because 0 means never lock out. One setting, two rules, one finding.'
            Change   = @{ LockoutThreshold = 0 }
            Expected = @('LockoutThreshold')
        }
        @{
            Name     = 'two rules for one setting: above the upper one'
            Why      = 'LockoutThreshold is 50: it passes "at least 1" and fails "at most 5". A script that stops at the first rule that names a setting never reaches the second.'
            Change   = @{ LockoutThreshold = 50 }
            Expected = @('LockoutThreshold')
        }
        @{
            Name     = 'numbers stored as text'
            Why      = 'The export holds "9", "90" and "3" as text. Compared as text, "9" is more than "14" and "90" is more than "365". Only the password length of 9 misses.'
            Change   = @{ MinimumPasswordLength = '9'; MaximumPasswordAgeDays = '90'; LockoutThreshold = '3' }
            Expected = @('MinimumPasswordLength')
        }
    )
}
