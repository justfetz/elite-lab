# A plausible but wrong solution: it compares correctly, but only against the first rule
# that names a setting. A setting with two rules is never checked against the second.
# The checker must fail it.
param(
    [Parameter(Mandatory = $true)]
    [string] $Path
)

$baseline = Get-Content -LiteralPath (Join-Path $Path 'baseline.json') -Raw | ConvertFrom-Json
$settings = Get-Content -LiteralPath (Join-Path $Path 'settings.json') -Raw | ConvertFrom-Json

$invariant = [System.Globalization.CultureInfo]::InvariantCulture
$done = New-Object System.Collections.Generic.List[string]

foreach ($rule in $baseline) {
    if ($done.Contains($rule.name)) {
        continue
    }
    $done.Add($rule.name)
    $ok = $false
    $property = $settings.PSObject.Properties[$rule.name]
    if ($null -ne $property) {
        $value = $property.Value
        if ($rule.rule -eq 'equals') {
            $ok = ($value -is $rule.value.GetType()) -and ($value -eq $rule.value)
        }
        else {
            $number = 0.0
            $isNumber = [double]::TryParse([string]$value, [System.Globalization.NumberStyles]::Float, $invariant, [ref]$number)
            if ($isNumber -and $rule.rule -eq 'atLeast') {
                $ok = $number -ge [double]$rule.value
            }
            elseif ($isNumber -and $rule.rule -eq 'atMost') {
                $ok = $number -le [double]$rule.value
            }
        }
    }
    if (-not $ok) {
        $rule.name
    }
}
