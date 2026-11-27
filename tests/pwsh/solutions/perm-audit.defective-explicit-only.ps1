# A plausible but wrong solution: on Windows it skips the entries a file inherits from its
# folder, as if only a file's own entries counted. Elsewhere it reports folders as well as
# files. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$root = (Resolve-Path -LiteralPath $Path).ProviderPath.TrimEnd('\', '/')
$onWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
$broad = 'S-1-1-0', 'S-1-5-11', 'S-1-5-32-545'

if ($onWindows) {
    $items = Get-ChildItem -LiteralPath $root -Recurse -File
}
else {
    $items = Get-ChildItem -LiteralPath $root -Recurse
}

foreach ($item in $items) {
    $overShared = $false
    if ($onWindows) {
        $writeData = [System.Security.AccessControl.FileSystemRights]::WriteData
        foreach ($rule in (Get-Acl -LiteralPath $item.FullName).Access) {
            if ($rule.IsInherited) {
                continue
            }
            $sid = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
            if ([string]$rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $writeData) -ne 0 -and $broad -contains $sid) {
                $overShared = $true
            }
        }
    }
    else {
        $overShared = $item.UnixMode[8] -eq 'w'
    }
    if ($overShared) {
        $item.FullName.Substring($root.Length + 1).Replace('\', '/')
    }
}
