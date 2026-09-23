try {
    Invoke-WebRequest -Uri 'https://legalai-backend-6jio.onrender.com/api/v1/health' -Method OPTIONS -Headers @{'Origin'='https://frontend-mocha-six-92.vercel.app';'Access-Control-Request-Method'='GET'} -ErrorAction Stop
} catch {
    $err = $_.Exception.Response
    Write-Host "Status: $($err.StatusCode)"
    $collection = $err.Headers
    foreach ($h in $collection.AllKeys) {
        if ($h -match 'access-control|vary') {
            Write-Host "$h : $($collection[$h])"
        }
    }
}
