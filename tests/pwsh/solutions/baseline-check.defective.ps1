# A plausible but wrong solution: it compares whatever it finds, as it finds it. A missing
# setting passes an atMost rule ($null -le 365 is true), and numbers that arrive as text
# are compared as text. The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$baseline = Get-Content -LiteralPath (Join-Path $Path 'baseline.json') -Raw | ConvertFrom-Json
$settings = Get-Content -LiteralPath (Join-Path $Path 'settings.json') -Raw | ConvertFrom-Json

foreach ($rule in $baseline) {
    $value = $settings.($rule.name)
    $ok = $true
    if ($rule.rule -eq 'atLeast') {
        $ok = $value -ge $rule.value
    }
    elseif ($rule.rule -eq 'atMost') {
        $ok = $value -le $rule.value
    }
    elseif ($rule.rule -eq 'equals') {
        $ok = $value -eq $rule.value
    }
    if (-not $ok) {
        $rule.name
    }
}
