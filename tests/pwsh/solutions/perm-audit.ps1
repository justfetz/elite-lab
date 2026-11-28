# Reference solution for the perm-audit checker. The tests prove it passes every case.
# One script for both worlds: access lists on Windows, modes on Linux and macOS.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$root = (Resolve-Path -LiteralPath $Path).ProviderPath.TrimEnd('\', '/')
$onWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
$broad = 'S-1-1-0', 'S-1-5-11', 'S-1-5-32-545'

foreach ($file in (Get-ChildItem -LiteralPath $root -Recurse -File)) {
    $overShared = $false
    if ($onWindows) {
        $writeData = [System.Security.AccessControl.FileSystemRights]::WriteData
        foreach ($rule in (Get-Acl -LiteralPath $file.FullName).Access) {
            if ([string]$rule.AccessControlType -ne 'Allow') {
                continue
            }
            if (($rule.FileSystemRights -band $writeData) -eq 0) {
                continue
            }
            $sid = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
            if ($broad -contains $sid) {
                $overShared = $true
            }
        }
    }
    else {
        $overShared = $file.UnixMode[8] -eq 'w'
    }
    if ($overShared) {
        $file.FullName.Substring($root.Length + 1).Replace('\', '/')
    }
}
