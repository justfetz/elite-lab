# Checker: find the failed-logon burst in a sample event export.
#
# The fixture is one CSV file of invented logon events on documentation addresses
# (RFC 5737). Nothing here reads the Security log. The events sit on 14 January so
# that no clock change anywhere falls inside the data.
#
# A series is a run of events from one source: Start (UTC time of day) and either
# Repeat and Step (that many events, Step seconds apart) or Offsets (seconds after Start).

$officeNoise = @(
    @{ Ip = '10.10.0.21'; Id = 4624; User = 'dana'; Start = '07:58:10'; Repeat = 4; Step = 1900 }
    @{ Ip = '10.10.0.34'; Id = 4624; User = 'miguel'; Start = '08:02:40'; Repeat = 5; Step = 1300 }
    @{ Ip = '10.10.0.21'; Id = 4625; User = 'dana'; Start = '08:31:05'; Repeat = 2; Step = 9 }
    @{ Ip = '198.51.100.20'; Id = 4625; User = 'administrator'; Start = '08:10:00'; Repeat = 3; Step = 1200 }
    @{ Ip = '192.0.2.44'; Id = 4625; User = 'svc_backup'; Start = '09:12:30'; Repeat = 2; Step = 400 }
)

@{
    Id         = 'logon-burst'
    Title      = 'Find the failed-logon burst'
    Goal       = 'Read an exported list of logon events and print every source address that has a burst of failed logons.'
    ScriptName = 'Find-LogonBurst.ps1'

    Brief      = @(
        'The fixture is logons.csv: one logon event per row, with the columns TimeCreated'
        '(UTC, written like 2026-01-14T08:15:04Z), EventId (4624 is a logon that worked,'
        '4625 is one that failed), TargetUserName, IpAddress and LogonType. The rows are'
        'not always in time order.'
        ''
        'A burst is 10 or more FAILED logons from one IpAddress, with no more than 300'
        'seconds between the first and the last of them.'
        ''
        'Print the IpAddress of every source that has a burst, once each.'
    )

    Starter    = @'
<#
Find-LogonBurst.ps1 - find the failed-logon burst in a sample event export.
The rules are in START_HERE.txt, next to this file.
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$rows = Import-Csv -LiteralPath (Join-Path $Path 'logons.csv')

# TODO: print the IpAddress of every source with a burst, one per line.
# A time such as 2026-01-14T08:15:04Z becomes a value you can subtract with:
#   [datetimeoffset]::Parse($row.TimeCreated, [cultureinfo]::InvariantCulture)
'@

    Debrief    = 'Event 4625 with a source address is how password guessing shows up. A count per source finds the loud ones; a sliding window finds the burst without drowning in slow background noise, and the same window over distinct user names catches password spraying. On a real machine the rows come from Get-WinEvent -FilterHashtable @{LogName=''Security'';Id=4625}.'

    Build      = {
        param($CasePath, $Case, $Definition)
        $null = $Definition
        $day = New-Object System.DateTime 2026, 1, 14, 0, 0, 0, ([System.DateTimeKind]::Utc)
        $invariant = [System.Globalization.CultureInfo]::InvariantCulture
        $rows = New-Object System.Collections.Generic.List[object]
        foreach ($series in @($Case.Series)) {
            $offsets = @()
            if ($series.ContainsKey('Offsets')) {
                $offsets = @($series.Offsets)
            }
            else {
                for ($i = 0; $i -lt $series.Repeat; $i++) {
                    $offsets += $i * $series.Step
                }
            }
            $start = [timespan]::Parse($series.Start, $invariant)
            foreach ($offset in $offsets) {
                $when = $day.Add($start).AddSeconds($offset)
                $rows.Add([pscustomobject][ordered]@{
                        TimeCreated    = $when.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", $invariant)
                        EventId        = $series.Id
                        TargetUserName = $series.User
                        IpAddress      = $series.Ip
                        LogonType      = 3
                    })
            }
        }
        $ordered = @($rows | Sort-Object -Property TimeCreated, IpAddress)
        if ($Case.ContainsKey('Shuffle') -and $Case.Shuffle) {
            # the same scrambled order every time: no randomness in a fixture
            $keyed = for ($i = 0; $i -lt $ordered.Count; $i++) {
                [pscustomobject]@{ Key = ($i * 7919 + 13) % 1009; Index = $i; Row = $ordered[$i] }
            }
            $ordered = @($keyed | Sort-Object -Property Key, Index | ForEach-Object { $_.Row })
        }
        $csv = @($ordered | ConvertTo-Csv -NoTypeInformation)
        Write-EliteTextFile -Path (Join-Path $CasePath 'logons.csv') -Text (($csv -join "`r`n") + "`r`n")
    }

    Sample     = @{
        Name   = 'sample'
        Series = @($officeNoise + @(
                @{ Ip = '203.0.113.7'; Id = 4625; User = 'administrator'; Start = '08:15:04'; Repeat = 12; Step = 10 }
            ))
    }

    Cases      = @(
        @{
            Name     = 'a quiet morning'
            Why      = 'Ordinary noise: a few failures per source, far apart, among logons that worked. Nothing is a burst.'
            Series   = $officeNoise
            Expected = @()
        }
        @{
            Name     = 'one loud source'
            Why      = 'Twelve failures from 203.0.113.7 in under two minutes, among the ordinary noise.'
            Series   = @($officeNoise + @(
                    @{ Ip = '203.0.113.7'; Id = 4625; User = 'administrator'; Start = '08:15:04'; Repeat = 12; Step = 10 }
                ))
            Expected = @('203.0.113.7')
        }
        @{
            Name     = 'thirty failures, never ten in five minutes'
            Why      = '198.51.100.77 fails thirty times, two minutes apart. That is slow guessing, not a burst: a script that counts a source''s total flags it wrongly.'
            Series   = @($officeNoise + @(
                    @{ Ip = '198.51.100.77'; Id = 4625; User = 'administrator'; Start = '08:00:00'; Repeat = 30; Step = 120 }
                ))
            Expected = @()
        }
        @{
            Name     = 'logons that worked do not count, and nine is not ten'
            Why      = '10.10.0.31 logs on fifteen times in a minute and every one works (4624). 203.0.113.9 fails nine times, one short.'
            Series   = @($officeNoise + @(
                    @{ Ip = '10.10.0.31'; Id = 4624; User = 'svc_scan'; Start = '08:40:00'; Repeat = 15; Step = 4 }
                    @{ Ip = '203.0.113.9'; Id = 4625; User = 'guest'; Start = '09:01:00'; Repeat = 9; Step = 5 }
                ))
            Expected = @()
        }
        @{
            Name     = 'exactly on the edge'
            Why      = '192.0.2.10 has ten failures with exactly 300 seconds from first to last: a burst. 192.0.2.11 has ten spread over 301 seconds: not one.'
            Series   = @(
                @{ Ip = '192.0.2.10'; Id = 4625; User = 'administrator'; Start = '09:00:00'
                    Offsets = @(0, 30, 60, 90, 120, 150, 180, 210, 240, 300) }
                @{ Ip = '192.0.2.11'; Id = 4625; User = 'administrator'; Start = '09:10:00'
                    Offsets = @(0, 30, 60, 90, 120, 150, 180, 210, 240, 301) }
            )
            Expected = @('192.0.2.10')
        }
        @{
            Name     = 'a burst in the middle of a long day'
            Why      = '203.0.113.80 fails now and then from 07:10 to 11:00, and ten times in two minutes at 09:00. Its failures span hours, and its first ten are not the burst: only a window that slides over all of them finds it.'
            Series   = @($officeNoise + @(
                    @{ Ip = '203.0.113.80'; Id = 4625; User = 'administrator'; Start = '07:10:00'; Repeat = 4; Step = 1500 }
                    @{ Ip = '203.0.113.80'; Id = 4625; User = 'administrator'; Start = '09:00:00'; Repeat = 10; Step = 13 }
                    @{ Ip = '203.0.113.80'; Id = 4625; User = 'administrator'; Start = '10:00:00'; Repeat = 3; Step = 1800 }
                ))
            Expected = @('203.0.113.80')
        }
        @{
            Name     = 'two sources, rows out of order'
            Why      = 'The rows are shuffled. The burst from 203.0.113.50 straddles 08:05:00 (six failures before, four after), so fixed five-minute buckets miss it. 192.0.2.99 fails twelve times in two groups an hour apart: not a burst.'
            Shuffle  = $true
            Series   = @($officeNoise + @(
                    @{ Ip = '203.0.113.50'; Id = 4625; User = 'administrator'; Start = '08:03:10'; Repeat = 10; Step = 20 }
                    @{ Ip = '198.51.100.5'; Id = 4625; User = 'root'; Start = '09:40:00'; Repeat = 14; Step = 15 }
                    @{ Ip = '192.0.2.99'; Id = 4625; User = 'admin'; Start = '08:20:00'; Repeat = 6; Step = 8 }
                    @{ Ip = '192.0.2.99'; Id = 4625; User = 'admin'; Start = '09:30:00'; Repeat = 6; Step = 8 }
                ))
            Expected = @('203.0.113.50', '198.51.100.5')
        }
    )
}
