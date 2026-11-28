# Checker: find the files with over-broad permissions in a fixture tree.
#
# The fixture is a small folder tree under the temp folder. On Windows each file gets
# its own access list; on Linux and macOS each gets a mode. The only permissions this
# file ever sets are on the files it has just created there.
#
# A tree entry names a path and an access level. The level table below says what that
# level means on each platform, so one case describes both.

@{
    Id           = 'perm-audit'
    Title        = 'Find the over-shared files'
    Goal         = 'Walk a folder tree and print the path of every file that too many people can change.'
    ScriptName   = 'Find-BroadPermission.ps1'

    Brief        = @(
        'The fixture is a folder tree of files. Find the files that too many people can'
        'change. Only files count, not folders.'
        ''
        'Print the path of every such file, relative to -Path, such as finance/payroll.csv.'
        'Either kind of slash works.'
    )

    BriefWindows = @(
        ''
        'On Windows a file is over-shared when its access list ALLOWS one of these to write:'
        '  Everyone (S-1-1-0), Authenticated Users (S-1-5-11) or BUILTIN\Users (S-1-5-32-545)'
        'To write means the rights include WriteData. Write, Modify and FullControl do;'
        'Read and ReadAndExecute do not. A Deny entry is not a grant. An entry the file'
        'inherits from its folder counts like any other.'
        ''
        'Read the list with (Get-Acl <file>).Access. Group names are translated on a'
        'non-English Windows; the SIDs above are not:'
        '  $rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value'
    )

    BriefUnix    = @(
        ''
        'On Linux and macOS a file is over-shared when "others" may write it: a w in the'
        'last of the three rwx groups, whatever stands beside it (rw-, -w- and rwx all count).'
        'A file only its group can write is not over-shared, and a folder is not a file.'
        ''
        'Read the mode with (Get-Item <file>).UnixMode.'
    )

    Starter      = @'
<#
Find-BroadPermission.ps1 - find the files with over-broad permissions in a folder tree.
The rules are in START_HERE.txt, next to this file.
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$files = Get-ChildItem -LiteralPath $Path -Recurse -File

# TODO: print the path of every over-shared file, relative to $Path, one per line.
foreach ($file in $files) {
}
'@

    Debrief      = 'Over-broad write access is how one compromised account becomes many changed files: a login script, a scheduled job''s program, a shared spreadsheet. The audit is always the same three questions - who, allowed or denied, and which rights - asked of every file, including the ones that only inherit their answer.'

    # What each access level means. Mode is for Linux and macOS; Grants are the entries
    # added on Windows, on top of full control for the file's owner.
    Access       = @{
        'owner-only'          = @{ Mode = '600'; Grants = @() }
        'everyone-read'       = @{ Mode = '644'; Grants = @(@{ Sid = 'S-1-1-0'; Rights = 'ReadAndExecute'; Type = 'Allow' }) }
        'everyone-modify'     = @{ Mode = '666'; Grants = @(@{ Sid = 'S-1-1-0'; Rights = 'Modify'; Type = 'Allow' }) }
        'authusers-full'      = @{ Mode = '777'; Grants = @(@{ Sid = 'S-1-5-11'; Rights = 'FullControl'; Type = 'Allow' }) }
        'users-write'         = @{ Mode = '646'; Grants = @(@{ Sid = 'S-1-5-32-545'; Rights = 'Write'; Type = 'Allow' }) }
        'users-modify'        = @{ Mode = '666'; Grants = @(@{ Sid = 'S-1-5-32-545'; Rights = 'Modify'; Type = 'Allow' }) }
        'users-write-only'    = @{ Mode = '662'; Grants = @(@{ Sid = 'S-1-5-32-545'; Rights = 'WriteData, AppendData'; Type = 'Allow' }) }
        'admins-full'         = @{ Mode = '660'; Grants = @(@{ Sid = 'S-1-5-32-544'; Rights = 'FullControl'; Type = 'Allow' }) }
        'everyone-deny-write' = @{
            Mode   = '444'
            Grants = @(
                @{ Sid = 'S-1-1-0'; Rights = 'Read'; Type = 'Allow' }
                @{ Sid = 'S-1-1-0'; Rights = 'Write'; Type = 'Deny' }
            )
        }
        'open-folder'         = @{ Mode = '777'; Grants = @() }
        'inherit'             = @{ Mode = '644'; Grants = @() }
    }

    Normalize    = {
        # a finding is a path relative to the case folder, with forward slashes
        param($Line, $CasePath)
        $text = ([string]$Line).Trim().Trim('"').Replace('\', '/')
        $root = ([string]$CasePath).Replace('\', '/').TrimEnd('/')
        if ($text.StartsWith($root + '/', [System.StringComparison]::OrdinalIgnoreCase)) {
            $text = $text.Substring($root.Length + 1)
        }
        while ($text.StartsWith('./')) {
            $text = $text.Substring(2)
        }
        $text.TrimStart('/')
    }

    Build        = {
        param($CasePath, $Case, $Definition)
        $onWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
        $separator = [string][System.IO.Path]::DirectorySeparatorChar
        if ($onWindows) {
            # Start from a folder that inherits nothing, so the temp folder's own access
            # list cannot leak into the fixture: only the owner, passed down to children.
            $owner = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
            $toChildren = [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
            $noPropagation = [System.Security.AccessControl.PropagationFlags]::None
            $rootAcl = New-Object System.Security.AccessControl.DirectorySecurity
            $rootAcl.SetAccessRuleProtection($true, $false)
            $rootAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule $owner, 'FullControl', $toChildren, $noPropagation, 'Allow'))
            Set-Acl -LiteralPath $CasePath -AclObject $rootAcl
        }
        else {
            $chmod = (Get-Command -Name chmod -CommandType Application | Select-Object -First 1).Path
            & $chmod 755 $CasePath
        }

        foreach ($entry in @($Case.Tree)) {
            $full = Join-Path $CasePath $entry.Path.Replace('/', $separator)
            $level = $Definition.Access[$entry.Access]
            $isFolder = $entry.ContainsKey('Kind') -and $entry.Kind -eq 'Folder'
            if ($isFolder) {
                $null = [System.IO.Directory]::CreateDirectory($full)
            }
            else {
                Write-EliteTextFile -Path $full -Text ("fixture file {0}`n" -f $entry.Path)
            }

            if (-not $onWindows) {
                & $chmod $level.Mode $full
                continue
            }
            if ($entry.Access -eq 'inherit') {
                continue        # the file keeps what its folder hands down
            }
            if ($isFolder) {
                $acl = New-Object System.Security.AccessControl.DirectorySecurity
                $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule $owner, 'FullControl', $toChildren, $noPropagation, 'Allow'))
            }
            else {
                $acl = New-Object System.Security.AccessControl.FileSecurity
                $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule $owner, 'FullControl', 'Allow'))
            }
            $acl.SetAccessRuleProtection($true, $false)
            foreach ($grant in @($level.Grants)) {
                $who = New-Object System.Security.Principal.SecurityIdentifier $grant.Sid
                if ($isFolder) {
                    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule $who, $grant.Rights, $toChildren, $noPropagation, $grant.Type
                }
                else {
                    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule $who, $grant.Rights, $grant.Type
                }
                $acl.AddAccessRule($rule)
            }
            Set-Acl -LiteralPath $full -AclObject $acl
        }
    }

    Sample       = @{
        Name = 'sample'
        Tree = @(
            @{ Path = 'readme.txt'; Access = 'everyone-read' }
            @{ Path = 'finance/budget.xlsx'; Access = 'owner-only' }
            @{ Path = 'finance/payroll.csv'; Access = 'everyone-modify' }
            @{ Path = 'ops/runbook.md'; Access = 'admins-full' }
        )
    }

    Cases        = @(
        @{
            Name     = 'a tidy share'
            Why      = 'Everyone may read two of these files and nobody beyond the owner and the administrators may change any. Being able to read is not over-sharing.'
            Tree     = @(
                @{ Path = 'readme.txt'; Access = 'everyone-read' }
                @{ Path = 'finance/budget.xlsx'; Access = 'owner-only' }
                @{ Path = 'finance/forecast.csv'; Access = 'admins-full' }
                @{ Path = 'hr/handbook.pdf'; Access = 'everyone-read' }
            )
            Expected = @()
        }
        @{
            Name     = 'one file anyone can change'
            Why      = 'finance/payroll.csv is writable by Everyone. The files around it are not.'
            Tree     = @(
                @{ Path = 'readme.txt'; Access = 'everyone-read' }
                @{ Path = 'finance/budget.xlsx'; Access = 'owner-only' }
                @{ Path = 'finance/payroll.csv'; Access = 'everyone-modify' }
                @{ Path = 'hr/handbook.pdf'; Access = 'everyone-read' }
            )
            Expected = @('finance/payroll.csv')
        }
        @{
            Name     = 'a file that is protected, next to one that is not'
            Why      = 'ops/runbook.md is read-only for everyone (on Windows: Everyone appears in a Deny entry for Write, which protects the file). Only ops/old-passwords.txt is a finding.'
            Tree     = @(
                @{ Path = 'ops/runbook.md'; Access = 'everyone-deny-write' }
                @{ Path = 'ops/old-passwords.txt'; Access = 'users-write' }
                @{ Path = 'ops/contacts.txt'; Access = 'everyone-read' }
            )
            Expected = @('ops/old-passwords.txt')
        }
        @{
            Name     = 'four ways to be too broad'
            Why      = 'Four files, four different ways in. On Windows: Everyone, Authenticated Users and BUILTIN\Users, and BUILTIN\Users once more with nothing but the right to write data. Elsewhere: modes 666, 777, 646 and 662, where others may write and not read. A script that looks for one of them finds one of four. The administrators'' file is fine.'
            Tree     = @(
                @{ Path = 'share/everyone.txt'; Access = 'everyone-modify' }
                @{ Path = 'share/authenticated.txt'; Access = 'authusers-full' }
                @{ Path = 'share/users.txt'; Access = 'users-write' }
                @{ Path = 'share/inbox.log'; Access = 'users-write-only' }
                @{ Path = 'share/admins.txt'; Access = 'admins-full' }
                @{ Path = 'share/private.txt'; Access = 'owner-only' }
            )
            Expected = @('share/everyone.txt', 'share/authenticated.txt', 'share/users.txt', 'share/inbox.log')
        }
        @{
            Name     = 'deep in the tree'
            Why      = 'The one finding is five folders down. Search the whole tree: Get-ChildItem -Recurse -File.'
            Tree     = @(
                @{ Path = 'projects/readme.txt'; Access = 'everyone-read' }
                @{ Path = 'projects/2026/plan.docx'; Access = 'owner-only' }
                @{ Path = 'projects/2026/q1/archive/old/notes.txt'; Access = 'authusers-full' }
                @{ Path = 'projects/2026/q1/summary.txt'; Access = 'admins-full' }
            )
            Expected = @('projects/2026/q1/archive/old/notes.txt')
        }
        @{
            Name     = 'handed down from the folder'
            Platform = 'Windows'
            Why      = 'team/plan.docx has no entry of its own: BUILTIN\Users may modify it because the team folder says so and the file inherits it. An inherited entry is as real as any other.'
            Tree     = @(
                @{ Path = 'team'; Kind = 'Folder'; Access = 'users-modify' }
                @{ Path = 'team/plan.docx'; Access = 'inherit' }
                @{ Path = 'solo/plan.docx'; Access = 'owner-only' }
            )
            Expected = @('team/plan.docx')
        }
        @{
            Name     = 'an open folder is not an open file'
            Platform = 'Unix'
            Why      = 'The dropbox folder is world-writable, but only one file inside it is. Folders are not findings, and a file is judged by its own mode.'
            Tree     = @(
                @{ Path = 'dropbox'; Kind = 'Folder'; Access = 'open-folder' }
                @{ Path = 'dropbox/readme.txt'; Access = 'everyone-read' }
                @{ Path = 'dropbox/upload.tmp'; Access = 'everyone-modify' }
            )
            Expected = @('dropbox/upload.tmp')
        }
    )
}
