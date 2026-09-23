$renderApiKey = $env:RENDER_API_KEY
if (-not $renderApiKey) {
    Write-Host "RENDER_API_KEY environment variable is not set."
    exit 1
}
$headers = @{
    'Authorization' = "Bearer $renderApiKey"
}
$deploy = Invoke-RestMethod -Uri 'https://api.render.com/v1/services/srv-daombs142hec738rd9r0/deploys' -Headers $headers -Method POST
Write-Host "Deploy ID: $($deploy.id)"
Write-Host "Status: $($deploy.status)"
