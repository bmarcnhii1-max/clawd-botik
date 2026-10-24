$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$modelDir = Join-Path $root "models"
$modelPath = Join-Path $modelDir "gemma-4-E2B-it-Q4_K_M.gguf"
$modelUrl = "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf"
$expectedSize = 3106738272

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama is not installed or not in PATH"
}

New-Item -ItemType Directory -Force -Path $modelDir | Out-Null

if (Test-Path $modelPath) {
    $size = (Get-Item -LiteralPath $modelPath).Length
    if ($size -ne $expectedSize) {
        Write-Host "Existing model has unexpected size ($size bytes); removing it"
        Remove-Item -LiteralPath $modelPath -Force
    }
}

if (-not (Test-Path $modelPath)) {
    $partPath = "$modelPath.part"
    if (Test-Path $partPath) {
        Remove-Item -LiteralPath $partPath -Force
    }
    Write-Host "Downloading Gemma 4 E2B Q4_K_M (about 3.1 GB)..."
    try {
        & curl.exe -L --fail --retry 3 --retry-delay 2 --continue-at - -o $partPath $modelUrl
        if ($LASTEXITCODE -ne 0) { throw "Model download failed" }
        $size = (Get-Item -LiteralPath $partPath).Length
        if ($size -ne $expectedSize) {
            throw "Downloaded model has unexpected size: $size (expected $expectedSize)"
        }
        Move-Item -LiteralPath $partPath -Destination $modelPath
    } catch {
        if (Test-Path $partPath) {
            Remove-Item -LiteralPath $partPath -Force
        }
        throw
    }
}

Push-Location $root
try {
    & ollama create gemma4-e2b-local -f Modelfile
    if ($LASTEXITCODE -ne 0) { throw "ollama create failed" }
} finally {
    Pop-Location
}

Write-Host "Local model ready: gemma4-e2b-local"
