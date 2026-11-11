# CareerForge AI — PowerShell Startup Script (Windows)
# Run from the project root: .\start.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CareerForge AI — Interview Trainer    " -ForegroundColor Cyan
Write-Host "  IBM Granite + watsonx.ai + RAG        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Check .env ──────────────────────────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found." -ForegroundColor Red
    Write-Host "Run: Copy-Item .env.example .env" -ForegroundColor Yellow
    Write-Host "Then add your WATSONX_API_KEY and WATSONX_PROJECT_ID." -ForegroundColor Yellow
    exit 1
}

$envContent = Get-Content ".env" -Raw
if ($envContent -match "your_ibm_cloud_api_key_here") {
    Write-Host "WARNING: IBM credentials not set in .env" -ForegroundColor Yellow
    Write-Host "App will run in DEGRADED MODE (fallback questions, no real Granite)." -ForegroundColor Yellow
    Write-Host "To enable full IBM Granite: edit .env with your real credentials." -ForegroundColor Yellow
    Write-Host ""
}

# ── Check Python ─────────────────────────────────────────────────────────────
$pythonVersion = python --version 2>&1
Write-Host "Python: $pythonVersion" -ForegroundColor Green

# ── Check dependencies ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Checking core dependencies..." -ForegroundColor Cyan
$coreDeps = @("fastapi", "uvicorn", "pydantic", "sqlalchemy")
$missing = @()
foreach ($dep in $coreDeps) {
    $check = python -c "import $dep" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missing += $dep
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing packages: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy python-dotenv python-multipart
    Write-Host ""
}

# ── Load knowledge base (first run) ──────────────────────────────────────────
$chromaPath = "backend\data\chroma_db"
if (-not (Test-Path $chromaPath) -or (Get-ChildItem $chromaPath -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0) {
    Write-Host "First run: loading knowledge base into ChromaDB..." -ForegroundColor Cyan
    Write-Host "(This requires IBM credentials for full embeddings; skipped in degraded mode)" -ForegroundColor Gray
    try {
        python -m backend.rag.corpus_loader
        Write-Host "Knowledge base loaded." -ForegroundColor Green
    } catch {
        Write-Host "Knowledge base load skipped (running in degraded mode)." -ForegroundColor Yellow
    }
}

# ── Start backend ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Starting CareerForge AI backend..." -ForegroundColor Green
Write-Host "  API:      http://localhost:8000" -ForegroundColor White
Write-Host "  Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Health:   http://localhost:8000/health" -ForegroundColor White
Write-Host "  Frontend: Open frontend\index.html in your browser" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
