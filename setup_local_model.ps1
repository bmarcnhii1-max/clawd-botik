$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$modelDir = Join-Path $root "models"
$modelPath = Join-Path $modelDir "gemma-4-E2B-it-Q4_K_M.gguf"
$modelUrl = "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf"

New-Item -ItemType Directory -Force -Path $modelDir | Out-Null
if (-not (Test-Path $modelPath)) {
    Write-Host "Downloading Gemma 4 E2B Q4_K_M (about 3.1 GB)..."
    & curl.exe -L --fail --retry 3 --retry-delay 2 -o $modelPath $modelUrl
    if ($LASTEXITCODE -ne 0) { throw "Model download failed" }
}

Push-Location $root
try {
    & ollama create gemma4-e2b-local -f Modelfile
    if ($LASTEXITCODE -ne 0) { throw "ollama create failed" }
} finally {
    Pop-Location
}

Write-Host "Local model ready: gemma4-e2b-local"
