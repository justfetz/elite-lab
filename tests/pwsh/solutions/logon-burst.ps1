# Reference solution for the logon-burst checker. The tests prove it passes every case.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$rows = Import-Csv -LiteralPath (Join-Path $Path 'logons.csv')
$failed = @($rows | Where-Object { $_.EventId -eq '4625' })

foreach ($source in ($failed | Group-Object -Property IpAddress)) {
    $times = @($source.Group |
            ForEach-Object { [datetimeoffset]::Parse($_.TimeCreated, [cultureinfo]::InvariantCulture) } |
            Sort-Object)
    $burst = $false
    # a sliding window: is any failure followed by its ninth successor within 300 seconds?
    for ($i = 0; ($i + 9) -lt $times.Count; $i++) {
        if (($times[$i + 9] - $times[$i]).TotalSeconds -le 300) {
            $burst = $true
            break
        }
    }
    if ($burst) {
        $source.Name
    }
}
