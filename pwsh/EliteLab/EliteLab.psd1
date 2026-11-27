@{
    RootModule           = 'EliteLab.psm1'
    ModuleVersion        = '0.1.0'
    GUID                 = '7b0c2f64-5d0a-4f0e-9a52-3c1e8f2d6a41'
    Author               = 'Jason Fetzer'
    CompanyName          = 'elite-lab'
    Copyright            = '(c) Jason Fetzer. MIT License.'
    Description          = 'A native elite command for PowerShell, elite doctor as objects, and blue-team checkers that run your audit script against fixture cases. The PowerShell side of elite-lab, a terminal training range for security skills.'

    PowerShellVersion    = '5.1'
    CompatiblePSEditions = @('Desktop', 'Core')

    FunctionsToExport    = @(
        'Invoke-Elite'
        'Test-EliteSetup'
        'Get-EliteChecker'
        'Start-EliteChecker'
        'Test-EliteChecker'
    )
    AliasesToExport      = @('elite')
    CmdletsToExport      = @()
    VariablesToExport    = @()

    PrivateData          = @{
        PSData = @{
            Tags       = @('security', 'training', 'blue-team', 'cli')
            LicenseUri = 'https://github.com/justfetz/elite-lab/blob/main/LICENSE'
            ProjectUri = 'https://github.com/justfetz/elite-lab'
        }
    }
}
