param(
    [Parameter(Position=0)]
    [string]$ToAddress
)

if ($ToAddress) {
    node "$PSScriptRoot\withdraw.mjs" $ToAddress
} else {
    node "$PSScriptRoot\withdraw.mjs"
}
