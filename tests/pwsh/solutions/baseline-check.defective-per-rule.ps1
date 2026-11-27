# A plausible but wrong solution: every comparison is right, but it prints a name once for
# every rule the setting breaks. A missing setting that two rules name is printed twice.
# The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$baseline = Get-Content -LiteralPath (Join-Path $Path 'baseline.json') -Raw | ConvertFrom-Json
$settings = Get-Content -LiteralPath (Join-Path $Path 'settings.json') -Raw | ConvertFrom-Json

foreach ($rule in $baseline) {
    $property = $settings.PSObject.Properties[$rule.name]
    if ($null -eq $property) {
        $rule.name
        continue
    }
    if ($rule.rule -eq 'atLeast' -and [double]$property.Value -lt [double]$rule.value) {
        $rule.name
    }
    elseif ($rule.rule -eq 'atMost' -and [double]$property.Value -gt [double]$rule.value) {
        $rule.name
    }
    elseif ($rule.rule -eq 'equals' -and $property.Value -ne $rule.value) {
        $rule.name
    }
}
