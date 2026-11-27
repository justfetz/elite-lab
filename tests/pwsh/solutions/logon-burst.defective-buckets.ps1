# A plausible but wrong solution: it cuts the day into fixed five-minute buckets and counts
# the failures in each. A burst that starts in one bucket and ends in the next is split in
# two and missed. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$failed = @(Import-Csv -LiteralPath (Join-Path $Path 'logons.csv') | Where-Object { $_.EventId -eq '4625' })
$found = New-Object System.Collections.Generic.List[string]

foreach ($bucket in ($failed | Group-Object -Property IpAddress, {
            $when = [datetimeoffset]::Parse($_.TimeCreated, [cultureinfo]::InvariantCulture)
            [math]::Floor($when.ToUnixTimeSeconds() / 300)
        })) {
    $address = $bucket.Group[0].IpAddress
    if ($bucket.Count -ge 10 -and -not $found.Contains($address)) {
        $found.Add($address)
    }
}

$found
