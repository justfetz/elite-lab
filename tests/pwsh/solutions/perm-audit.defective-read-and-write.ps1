# A plausible but wrong solution: it asks for more than the rule does. On Windows the group
# has to hold Write, Modify or FullControl by name, so a bare right to write data slips
# past; elsewhere "others" have to be able to read as well as write. The checker must fail it.
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
        foreach ($rule in (Get-Acl -LiteralPath $file.FullName).Access) {
            $sid = $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
            $named = ([string]$rule.FileSystemRights) -match '(^|, )(Write|Modify|FullControl)(,|$)'
            if ([string]$rule.AccessControlType -eq 'Allow' -and $named -and $broad -contains $sid) {
                $overShared = $true
            }
        }
    }
    else {
        $overShared = $file.UnixMode.Substring(7, 2) -eq 'rw'
    }
    if ($overShared) {
        $file.FullName.Substring($root.Length + 1).Replace('\', '/')
    }
}
