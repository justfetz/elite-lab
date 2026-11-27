# A plausible but wrong solution: no sliding window. It flags a source when it has ten or
# more failures in all and they all fit inside 300 seconds, so a burst in the middle of a
# long day slips past. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$failed = @(Import-Csv -LiteralPath (Join-Path $Path 'logons.csv') | Where-Object { $_.EventId -eq '4625' })

foreach ($source in ($failed | Group-Object -Property IpAddress)) {
    if ($source.Count -lt 10) {
        continue
    }
    $times = @($source.Group |
            ForEach-Object { [datetimeoffset]::Parse($_.TimeCreated, [cultureinfo]::InvariantCulture) } |
            Sort-Object)
    if (($times[-1] - $times[0]).TotalSeconds -le 300) {
        $source.Name
    }
}
