$renderApiKey = $env:RENDER_API_KEY
if (-not $renderApiKey) {
    Write-Host "RENDER_API_KEY environment variable is not set."
    exit 1
}
$headers = @{
    'Authorization' = "Bearer $renderApiKey"
    'Content-Type' = 'application/json'
}
$bodyPath = Join-Path $PSScriptRoot 'render-deploy.json'
if (-not (Test-Path $bodyPath)) {
    Write-Host "Payload file not found: $bodyPath"
    exit 1
}
$body = Get-Content -Raw -Path $bodyPath
$response = Invoke-RestMethod -Uri 'https://api.render.com/v1/services' -Headers $headers -Method POST -Body $body
$response | ConvertTo-Json -Depth 10
