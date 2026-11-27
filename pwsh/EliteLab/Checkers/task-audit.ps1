# Checker: flag the risky entries in an exported scheduled-task list.
#
# The fixture is one CSV file. Nothing here touches the Task Scheduler: the rows are
# invented, and the encoded command lines decode to Get-Date and Write-Output "hello".
# Each case isolates one rule, so a script that skips that rule fails that case only.

$quiet = @(
    @{ TaskName = 'ScheduledDefrag'; TaskPath = '\Microsoft\Windows\Defrag\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = '%windir%\system32\defrag.exe'; Arguments = '-c -h -k -g -$' }
    @{ TaskName = 'Schedule Scan'; TaskPath = '\Microsoft\Windows\UpdateOrchestrator\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = '%systemroot%\system32\usoclient.exe'; Arguments = 'StartScan' }
    @{ TaskName = 'BackupNightly'; TaskPath = '\Lakefront\'; State = 'Ready'; RunAs = 'LAKEFRONT\svc_backup'
        Execute = '"C:\Program Files\Lakefront\Backup\backup.exe"'; Arguments = '--target D:\Backups --quiet' }
    # -Encoding is not -enc, and -ExecutionPolicy is not -e
    @{ TaskName = 'LogRotate'; TaskPath = '\Lakefront\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = 'powershell.exe'; Arguments = '-NoProfile -File C:\Scripts\Rotate-Logs.ps1 -Encoding UTF8' }
    @{ TaskName = 'InventoryReport'; TaskPath = '\Lakefront\'; State = 'Disabled'; RunAs = 'LAKEFRONT\svc_inventory'
        Execute = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
        Arguments = '-NoProfile -ExecutionPolicy RemoteSigned -WindowStyle Normal -File "C:\Program Files\Lakefront\Inventory\report.ps1"' }
    # httpd.conf holds "http" but is not a URL
    @{ TaskName = 'ApacheReload'; TaskPath = '\Lakefront\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = '"C:\Program Files\Apache24\bin\httpd.exe"'; Arguments = '-k restart -f conf\httpd.conf' }
    # \Users\ in the middle of a path on another drive is not C:\Users\
    @{ TaskName = 'UserDirectorySync'; TaskPath = '\Lakefront\'; State = 'Ready'; RunAs = 'LAKEFRONT\svc_directory'
        Execute = 'D:\Apps\Users\dirsync.exe'; Arguments = '/full' }
)

$writableFolder = @(
    @{ TaskName = 'Updater'; TaskPath = '\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = 'C:\Users\Public\Libraries\updater.exe'; Arguments = '' }
    @{ TaskName = 'SyncHelper'; TaskPath = '\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = '"C:\ProgramData\SyncHelper\sync.exe"'; Arguments = '/background' }
    @{ TaskName = 'TelemetryCache'; TaskPath = '\Microsoft\Windows\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = 'c:\windows\temp\tc.exe'; Arguments = '' }
    @{ TaskName = 'ProfileTidy'; TaskPath = '\'; State = 'Ready'; RunAs = 'LAKEFRONT\dana'
        Execute = '%APPDATA%\Tidy\tidy.exe'; Arguments = '--silent' }
)

$hiddenCommand = @(
    @{ TaskName = 'HealthCheck'; TaskPath = '\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = 'powershell.exe'; Arguments = '-NoProfile -WindowStyle Hidden -File C:\Scripts\health.ps1' }
    @{ TaskName = 'DriverSync'; TaskPath = '\Microsoft\Windows\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = 'powershell.exe'
        Arguments = '-nop -w hidden -enc VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAiAGgAZQBsAGwAbwAiAA==' }
    @{ TaskName = 'FontCache'; TaskPath = '\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
        Arguments = '-EncodedCommand RwBlAHQALQBEAGEAdABlAA==' }
    @{ TaskName = 'Indexer'; TaskPath = '\'; State = 'Ready'; RunAs = 'LAKEFRONT\dana'
        Execute = 'pwsh.exe'; Arguments = '-e RwBlAHQALQBEAGEAdABlAA==' }
)

$network = @(
    @{ TaskName = 'PatchFetch'; TaskPath = '\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = 'powershell.exe'
        Arguments = '-NoProfile -Command "Invoke-WebRequest -Uri https://files.example.test/patch.ps1 -OutFile C:\Scripts\patch.ps1"' }
    @{ TaskName = 'HelpViewer'; TaskPath = '\'; State = 'Ready'; RunAs = 'LAKEFRONT\dana'
        Execute = 'mshta.exe'; Arguments = 'http://intranet.example.test/help.hta' }
    @{ TaskName = 'CertSync'; TaskPath = '\Lakefront\'; State = 'Ready'; RunAs = 'SYSTEM'
        Execute = 'certutil.exe'; Arguments = '-urlcache -f HTTP://pki.example.test/root.cer D:\Pki\root.cer' }
)

# one task, two broken rules: still one finding
$twoRules = @{ TaskName = 'WeeklySync'; TaskPath = '\'; State = 'Ready'; RunAs = 'SYSTEM'
    Execute = 'C:\Users\Public\sync.cmd'; Arguments = 'https://files.example.test/list.txt' }

@{
    Id         = 'task-audit'
    Title      = 'Flag the risky scheduled tasks'
    Goal       = 'Read an exported scheduled-task list and print the name of every task that breaks a rule.'
    ScriptName = 'Find-RiskyTask.ps1'

    Brief      = @(
        'The fixture is tasks.csv: one scheduled task per row, with the columns TaskName,'
        'TaskPath, State, RunAs, Execute and Arguments - what Get-ScheduledTask shows,'
        'saved with Export-Csv.'
        ''
        'Flag a task when ANY of these is true. Upper and lower case do not matter.'
        '  1. Its program runs from a folder any user can write to: Execute, with any'
        '     surrounding quotes removed, starts with C:\Users\, C:\ProgramData\ or'
        '     C:\Windows\Temp\, or with %TEMP%, %APPDATA%, %LOCALAPPDATA% or %PUBLIC%.'
        '  2. Its command line hides what it runs: Arguments holds -EncodedCommand, -enc'
        '     or -e as a whole word, or -WindowStyle Hidden (also written -w hidden).'
        '  3. Its command line reaches the network: Arguments holds http:// or https://.'
        ''
        'Print the TaskName of every flagged task, once each.'
    )

    Starter    = @'
<#
Find-RiskyTask.ps1 - flag the risky entries in an exported scheduled-task list.
The rules are in START_HERE.txt, next to this file.
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$tasks = Import-Csv -LiteralPath (Join-Path $Path 'tasks.csv')

# TODO: print the TaskName of every task that breaks a rule, one per line.
foreach ($task in $tasks) {
}
'@

    Debrief    = 'A scheduled task is the oldest way to keep running after a reboot, so the task list is one of the first places a defender looks. Where the program lives, how it is started and what it reaches say more than its name. On a real machine the same fields come from Get-ScheduledTask and its Actions.'

    Build      = {
        param($CasePath, $Case, $Definition)
        $null = $Definition
        $rows = foreach ($task in @($Case.Tasks)) {
            [pscustomobject][ordered]@{
                TaskName  = $task.TaskName
                TaskPath  = $task.TaskPath
                State     = $task.State
                RunAs     = $task.RunAs
                Execute   = $task.Execute
                Arguments = $task.Arguments
            }
        }
        $csv = @($rows | ConvertTo-Csv -NoTypeInformation)
        Write-EliteTextFile -Path (Join-Path $CasePath 'tasks.csv') -Text (($csv -join "`r`n") + "`r`n")
    }

    Sample     = @{
        Name  = 'sample'
        Tasks = @($quiet[0], $writableFolder[0], $quiet[3], $hiddenCommand[1], $quiet[2], $network[0], $quiet[5])
    }

    Cases      = @(
        @{
            Name     = 'a clean export'
            Why      = 'Nothing here is risky. A script that flags a row is matching too loosely: -Encoding is not -enc, -ExecutionPolicy is not -e, httpd.conf is not a URL, and D:\Apps\Users\ is not C:\Users\.'
            Tasks    = $quiet
            Expected = @()
        }
        @{
            Name     = 'program in a folder any user can write to'
            Why      = 'Rule 1 only. One path is quoted, one is lower case and one starts with %APPDATA%.'
            Tasks    = @($quiet[0], $writableFolder[0], $quiet[2], $writableFolder[1], $quiet[6], $writableFolder[2], $writableFolder[3], $quiet[1])
            Expected = @('Updater', 'SyncHelper', 'TelemetryCache', 'ProfileTidy')
        }
        @{
            Name     = 'command line that hides what it runs'
            Why      = 'Rule 2 only: -WindowStyle Hidden, -w hidden, -enc, -EncodedCommand and -e. The -Encoding, -ExecutionPolicy and -WindowStyle Normal rows must stay clean.'
            Tasks    = @($quiet[3], $hiddenCommand[0], $quiet[4], $hiddenCommand[1], $hiddenCommand[2], $quiet[0], $hiddenCommand[3])
            Expected = @('HealthCheck', 'DriverSync', 'FontCache', 'Indexer')
        }
        @{
            Name     = 'command line that reaches the network'
            Why      = 'Rule 3 only: http:// and https://, in any case. httpd.conf is a file name.'
            Tasks    = @($quiet[5], $network[0], $quiet[2], $network[1], $network[2], $quiet[1])
            Expected = @('PatchFetch', 'HelpViewer', 'CertSync')
        }
        @{
            Name     = 'all three rules in one export'
            Why      = 'Every rule at once, among ordinary tasks. WeeklySync breaks two rules and is still one finding.'
            Tasks    = @($quiet + $writableFolder + $hiddenCommand + $network + @($twoRules))
            Expected = @('Updater', 'SyncHelper', 'TelemetryCache', 'ProfileTidy', 'HealthCheck', 'DriverSync',
                'FontCache', 'Indexer', 'PatchFetch', 'HelpViewer', 'CertSync', 'WeeklySync')
        }
    )
}
