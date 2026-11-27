# A plausible but wrong solution: the permission test is right, but it looks only at the
# files directly inside the folder it is given and never goes into the folders below.
# The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$root = (Resolve-Path -LiteralPath $Path).ProviderPath.TrimEnd('\', '/')
$onWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
$broad = 'S-1-1-0', 'S-1-5-11', 'S-1-5-32-545'

foreach ($file in (Get-ChildItem -LiteralPath $root -File)) {
    $overShared = $false
    if ($onWindows) {
        $writeData = [System.Security.AccessControl.FileSystemRights]::WriteData
        foreach ($rule in (Get-Acl -LiteralPath $file.FullName).Access) {
            $sid = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
            if ([string]$rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $writeData) -ne 0 -and $broad -contains $sid) {
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
