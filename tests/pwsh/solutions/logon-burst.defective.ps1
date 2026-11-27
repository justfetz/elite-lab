# A plausible but wrong solution: it counts each source's failures and ignores time.
# The checker must fail it on the slow-guessing case.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

Import-Csv -LiteralPath (Join-Path $Path 'logons.csv') |
    Where-Object { $_.EventId -eq '4625' } |
    Group-Object -Property IpAddress |
    Where-Object { $_.Count -ge 10 } |
    ForEach-Object { $_.Name }
