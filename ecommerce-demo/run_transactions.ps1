# E-Commerce Demo - Transaction Generator
# Runs multiple transactions to populate Grafana dashboards

param(
    [int]$Count = 5,
    [int]$DelaySeconds = 3
)

Write-Host "Transaction Generator Started" -ForegroundColor Green
Write-Host ""

$customers = @("C001", "C002", "C003", "C004", "C005")
$skus = @("SKU-001", "SKU-002", "SKU-003", "SKU-005", "SKU-006", "SKU-007")

for ($i = 1; $i -le $Count; $i++) {
    $customer = $customers | Get-Random
    $sku1 = $skus | Get-Random
    $sku2 = $skus | Get-Random
    $qty1 = Get-Random -Minimum 1 -Maximum 3
    $qty2 = Get-Random -Minimum 0 -Maximum 2
    
    Write-Host "[$i/$Count] Running transaction..." -ForegroundColor Cyan
    Write-Host "  Customer: $customer"
    Write-Host "  SKU1: $sku1 x$qty1"
    if ($qty2 -gt 0) {
        Write-Host "  SKU2: $sku2 x$qty2"
    }
    
    $url = "http://localhost:8007/api/run?customer_id=$customer&sku1=$sku1&qty1=$qty1"
    if ($qty2 -gt 0) {
        $url = $url + "&sku2=$sku2&qty2=$qty2"
    }
    
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 60 -ErrorAction Stop
        Write-Host "  Status: OK - Transaction started" -ForegroundColor Green
    } catch {
        Write-Host "  Status: ERROR - $($_.Exception.Message)" -ForegroundColor Red
    }
    
    if ($i -lt $Count) {
        Write-Host "  Waiting ${DelaySeconds}s..." -ForegroundColor Gray
        Start-Sleep -Seconds $DelaySeconds
    }
    Write-Host ""
}

Write-Host "All transactions completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Wait 2-3 minutes for metrics collection"
Write-Host "2. Open Grafana: http://localhost:3000"
Write-Host "3. View dashboards"
Write-Host "4. Check Alertmanager: http://localhost:9093"
