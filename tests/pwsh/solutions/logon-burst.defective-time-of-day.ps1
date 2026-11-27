# A plausible but wrong solution: it reads the time of day out of TimeCreated and ignores
# the date, so a burst across midnight is missed and the same minute on two days looks
# like one burst. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$failed = @(Import-Csv -LiteralPath (Join-Path $Path 'logons.csv') | Where-Object { $_.EventId -eq '4625' })

foreach ($source in ($failed | Group-Object -Property IpAddress)) {
    $seconds = @($source.Group |
            ForEach-Object { [timespan]::Parse($_.TimeCreated.Substring(11, 8), [cultureinfo]::InvariantCulture).TotalSeconds } |
            Sort-Object)
    $burst = $false
    for ($i = 0; ($i + 9) -lt $seconds.Count; $i++) {
        if (($seconds[$i + 9] - $seconds[$i]) -le 300) {
            $burst = $true
        }
    }
    if ($burst) {
        $source.Name
    }
}
