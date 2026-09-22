$headers = @{
    'Authorization' = 'Bearer rnd_lE3iSPXmafR91B1X1KNG1EXvZbWT'
}
$deploy = Invoke-RestMethod -Uri 'https://api.render.com/v1/services/srv-daombs142hec738rd9r0/deploys' -Headers $headers -Method POST
Write-Host "Deploy ID: $($deploy.id)"
Write-Host "Status: $($deploy.status)"
