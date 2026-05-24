<#
.SYNOPSIS
    Run tests for the banking-demo service with coverage reporting.

.DESCRIPTION
    Executes pytest with coverage analysis and enforces 80-90% coverage gate.
    Supports both quick test runs and full coverage reports.

.PARAMETER Coverage
    If specified, run tests with coverage report and enforce 80% minimum.

.PARAMETER Verbose
    If specified, show verbose test output.

.EXAMPLE
    .\run-tests.ps1 -Coverage -Verbose
#>

param(
    [switch]$Coverage,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"

# Get the parent banking-demo directory
$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$banking_demo_dir = Split-Path -Parent $script_dir
$tests_dir = Join-Path $script_dir "tests"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Banking Demo — Test Runner" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Banking Demo Dir: $banking_demo_dir" -ForegroundColor Gray
Write-Host "Tests Dir: $tests_dir" -ForegroundColor Gray
Write-Host ""

# Check if pytest is available
try {
    $pytest_version = & pytest --version 2>"$null"
    Write-Host "✓ pytest found: $pytest_version" -ForegroundColor Green
} catch {
    Write-Host "✗ pytest not found. Install with: pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Running tests..." -ForegroundColor Cyan

# Build pytest command
$pytest_args = @("$tests_dir", "-v", "--tb=short")

if ($Coverage) {
    $pytest_args += @("--cov=banking_demo", "--cov-report=term-missing", "--cov-fail-under=80")
    Write-Host "Coverage gate: 80% minimum" -ForegroundColor Yellow
}

if ($Verbose) {
    $pytest_args += "-vv"
}

# Run tests
& pytest @pytest_args
$test_exit_code = $LASTEXITCODE

Write-Host ""
if ($test_exit_code -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Tests failed with exit code: $test_exit_code" -ForegroundColor Red
    exit $test_exit_code
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Test run complete" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
