$headers = @{
    'Authorization' = 'Bearer rnd_lE3iSPXmafR91B1X1KNG1EXvZbWT'
    'Content-Type' = 'application/json'
}
$body = Get-Content -Raw -Path 'C:\Users\ravin\Downloads\PROJECT\backend\render-deploy.json'
$response = Invoke-RestMethod -Uri 'https://api.render.com/v1/services' -Headers $headers -Method POST -Body $body
$response | ConvertTo-Json -Depth 10
