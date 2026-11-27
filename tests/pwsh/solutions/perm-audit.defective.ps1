# A plausible but wrong solution. On Windows it looks only for Everyone and does not ask
# whether the entry allows or denies. Elsewhere it treats group-writable as world-writable.
# The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$root = (Resolve-Path -LiteralPath $Path).ProviderPath.TrimEnd('\', '/')
$onWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT

foreach ($file in (Get-ChildItem -LiteralPath $root -Recurse -File)) {
    $overShared = $false
    if ($onWindows) {
        foreach ($rule in (Get-Acl -LiteralPath $file.FullName).Access) {
            $sid = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
            if ($sid -eq 'S-1-1-0' -and ([string]$rule.FileSystemRights) -match 'Write|Modify|FullControl') {
                $overShared = $true
            }
        }
    }
    else {
        $overShared = ($file.UnixMode[5] -eq 'w') -or ($file.UnixMode[8] -eq 'w')
    }
    if ($overShared) {
        $file.FullName.Substring($root.Length + 1).Replace('\', '/')
    }
}
