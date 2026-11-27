# PSScriptAnalyzer settings for the PowerShell in this repository (pwsh/ and tests/pwsh/).
#
#   Invoke-ScriptAnalyzer -Path . -Recurse -Settings ./PSScriptAnalyzerSettings.psd1
#
# Every rule the analyzer ships with runs, at every severity, and no rule is excluded.
# ParseError is in the list so that a file that does not parse is reported, not skipped.
# Two things are set on top of the defaults:
#
#   PSUseCompatibleSyntax      fails anything Windows PowerShell 5.1 cannot parse
#                              (a ternary, ??, &&), since the module supports 5.1 and 7.
#   PSAvoidUsingCmdletAliases  allows one alias, elite. It is the command the module
#                              exists to provide, and the tests call it by that name on
#                              purpose. The module's own code never uses it, or any other
#                              alias; tests/pwsh/EliteLab.Module.Tests.ps1 checks that.
@{
    IncludeDefaultRules = $true
    Severity            = @('ParseError', 'Error', 'Warning', 'Information')
    Rules               = @{
        PSUseCompatibleSyntax     = @{
            Enable         = $true
            TargetVersions = @('5.1', '7.0')
        }
        PSAvoidUsingCmdletAliases = @{
            allowlist = @('elite')
        }
    }
}
