$headers = @{
    'Origin' = 'https://frontend-mocha-six-92.vercel.app'
    'Access-Control-Request-Method' = 'GET'
}
try {
    $resp = Invoke-WebRequest -Uri 'https://legalai-backend-6jio.onrender.com/api/v1/health' -Method OPTIONS -Headers $headers
    Write-Host "Status: $($resp.StatusCode)"
    foreach ($key in $resp.Headers.Keys) {
        Write-Host "${key}: $($resp.Headers[$key])"
    }
} catch {
    Write-Host "Error: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        Write-Host "Status: $($_.Exception.Response.StatusCode)"
        foreach ($key in $_.Exception.Response.Headers.AllKeys) {
            Write-Host "${key}: $($_.Exception.Response.Headers[$key])"
        }
    }
}
