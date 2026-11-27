# A plausible but wrong solution: its windows do not slide. A window opens at a failure and
# holds everything within 300 seconds of it; the next window opens at the first failure
# after that. A burst that begins inside an open window is cut in two. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$failed = @(Import-Csv -LiteralPath (Join-Path $Path 'logons.csv') | Where-Object { $_.EventId -eq '4625' })

foreach ($source in ($failed | Group-Object -Property IpAddress)) {
    $times = @($source.Group |
            ForEach-Object { [datetimeoffset]::Parse($_.TimeCreated, [cultureinfo]::InvariantCulture) } |
            Sort-Object)
    $burst = $false
    $first = 0
    while ($first -lt $times.Count) {
        $next = $first
        while ($next -lt $times.Count -and ($times[$next] - $times[$first]).TotalSeconds -le 300) {
            $next++
        }
        if (($next - $first) -ge 10) {
            $burst = $true
        }
        $first = $next
    }
    if ($burst) {
        $source.Name
    }
}
