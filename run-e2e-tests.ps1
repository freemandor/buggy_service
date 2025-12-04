# Club Med Buggy Service - E2E Test Runner
# This script runs E2E tests in an isolated environment

Write-Host "=== Club Med Buggy Service - E2E Test Runner ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$TEST_DB = "backend/test_db.sqlite3"
$BACKEND_PORT = 8001
$FRONTEND_PORT = 5174
$API_URL = "http://localhost:$BACKEND_PORT"

# Cleanup function
function Cleanup {
    Write-Host "`n=== Cleaning up ===" -ForegroundColor Yellow
    
    if ($backendProcess) {
        Write-Host "Stopping test backend server..."
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    if ($frontendProcess) {
        Write-Host "Stopping test frontend server..."
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    
    # Kill any remaining processes on our test ports
    Get-NetTCPConnection -LocalPort $BACKEND_PORT -ErrorAction SilentlyContinue | 
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    
    Get-NetTCPConnection -LocalPort $FRONTEND_PORT -ErrorAction SilentlyContinue | 
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    
    Write-Host "Cleanup complete!" -ForegroundColor Green
}

# Register cleanup on script exit
trap { Cleanup; break }

try {
    # Step 1: Setup test database
    Write-Host "Step 1: Setting up test database..." -ForegroundColor Cyan
    
    if (Test-Path $TEST_DB) {
        Remove-Item $TEST_DB -Force
        Write-Host "  - Removed old test database" -ForegroundColor Gray
    }
    
    # Run migrations with test settings
    Write-Host "  - Running migrations..." -ForegroundColor Gray
    & backend\.venv\Scripts\python.exe backend\manage.py migrate --noinput --settings=buggy_project.settings_test
    if ($LASTEXITCODE -ne 0) { throw "Migration failed" }
    
    # Seed test data
    Write-Host "  - Seeding test data..." -ForegroundColor Gray
    & backend\.venv\Scripts\python.exe backend\manage.py seed_pois_and_edges --settings=buggy_project.settings_test
    if ($LASTEXITCODE -ne 0) { throw "Seeding failed" }
    
    Write-Host "  ✓ Test database ready" -ForegroundColor Green
    Write-Host ""
    
    # Step 2: Start test backend server
    Write-Host "Step 2: Starting test backend server on port $BACKEND_PORT..." -ForegroundColor Cyan
    
    $backendProcess = Start-Process -FilePath "backend\.venv\Scripts\python.exe" `
        -ArgumentList "backend\manage.py", "runserver", "0.0.0.0:$BACKEND_PORT", "--settings=buggy_project.settings_test" `
        -PassThru `
        -WindowStyle Hidden
    
    # Wait for backend to be ready
    Write-Host "  - Waiting for backend..." -ForegroundColor Gray
    $maxAttempts = 30
    $attempt = 0
    $backendReady = $false
    
    while ($attempt -lt $maxAttempts -and -not $backendReady) {
        Start-Sleep -Seconds 1
        try {
            $response = Invoke-WebRequest -Uri "$API_URL/api/auth/me/" -Method GET -ErrorAction Stop -TimeoutSec 2
            $backendReady = $true
        } catch {
            $attempt++
        }
    }
    
    if (-not $backendReady) {
        throw "Backend server failed to start"
    }
    
    Write-Host "  ✓ Test backend server running" -ForegroundColor Green
    Write-Host ""
    
    # Step 3: Start test frontend server
    Write-Host "Step 3: Starting test frontend server on port $FRONTEND_PORT..." -ForegroundColor Cyan
    
    # Update frontend .env for test
    $testEnv = "VITE_API_BASE=$API_URL/api"
    Set-Content -Path "frontend\.env.test" -Value $testEnv
    
    $frontendProcess = Start-Process -FilePath "npm.exe" `
        -ArgumentList "run", "dev", "--", "--port", $FRONTEND_PORT `
        -WorkingDirectory "frontend" `
        -PassThru `
        -WindowStyle Hidden
    
    # Wait for frontend to be ready
    Write-Host "  - Waiting for frontend..." -ForegroundColor Gray
    $attempt = 0
    $frontendReady = $false
    
    while ($attempt -lt $maxAttempts -and -not $frontendReady) {
        Start-Sleep -Seconds 1
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$FRONTEND_PORT" -Method GET -ErrorAction Stop -TimeoutSec 2
            $frontendReady = $true
        } catch {
            $attempt++
        }
    }
    
    if (-not $frontendReady) {
        throw "Frontend server failed to start"
    }
    
    Write-Host "  ✓ Test frontend server running" -ForegroundColor Green
    Write-Host ""
    
    # Step 4: Run E2E tests
    Write-Host "Step 4: Running E2E tests..." -ForegroundColor Cyan
    Write-Host ""
    
    # Set environment variables for Playwright
    $env:VITE_API_BASE = "$API_URL/api"
    $env:PLAYWRIGHT_BASE_URL = "http://localhost:$FRONTEND_PORT"
    
    Set-Location frontend
    & npm run test:e2e -- --config playwright.config.test.ts
    $testExitCode = $LASTEXITCODE
    Set-Location ..
    
    Write-Host ""
    if ($testExitCode -eq 0) {
        Write-Host "=== ✓ ALL TESTS PASSED ===" -ForegroundColor Green
    } else {
        Write-Host "=== ✗ TESTS FAILED ===" -ForegroundColor Red
    }
    
} catch {
    Write-Host "`nError: $_" -ForegroundColor Red
    $testExitCode = 1
} finally {
    Cleanup
    
    # Clean up test env file
    if (Test-Path "frontend\.env.test") {
        Remove-Item "frontend\.env.test" -Force
    }
    
    # Restore environment
    Remove-Item Env:\VITE_API_BASE -ErrorAction SilentlyContinue
    Remove-Item Env:\PLAYWRIGHT_BASE_URL -ErrorAction SilentlyContinue
}

Write-Host ""
exit $testExitCode

