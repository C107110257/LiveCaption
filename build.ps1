$desktopFolder = [Environment]::GetFolderPath("Desktop")
$desktopPath = Join-Path $desktopFolder "LiveCaption"
$publishPath = "\\192.168.0.240\project\Ken_Lin\LiveCaption"

Write-Host "Check LiveCaption..."

$proc = Get-Process -Name "LiveCaption" -ErrorAction SilentlyContinue

if ($proc) {

    Write-Host "LiveCaption is running!"
    Write-Host "Please close LiveCaption.exe first."

    exit 1
}

Write-Host "Locate faster_whisper assets..."

$fasterWhisperDir = python -c "import faster_whisper, os; print(os.path.dirname(faster_whisper.__file__))"

if (-not $fasterWhisperDir -or -not (Test-Path $fasterWhisperDir)) {
    Write-Host "Could not locate faster_whisper package. Is it installed in this environment?"
    exit 1
}

$fasterWhisperAssets = Join-Path $fasterWhisperDir "assets"

Write-Host "Found: $fasterWhisperAssets"

Write-Host "Clean build..."

if (Test-Path build) {
    Remove-Item build -Recurse -Force
}

Write-Host "Clean previous output (keep models/)..."

if (Test-Path "$desktopPath\LiveCaption.exe") {
    Remove-Item "$desktopPath\LiveCaption.exe" -Force
}

if (Test-Path "$desktopPath\_internal") {
    Remove-Item "$desktopPath\_internal" -Recurse -Force
}

if (Test-Path "$desktopPath\config.json") {
    Remove-Item "$desktopPath\config.json" -Force
}

Write-Host "Build..."

pyinstaller `
    --noconfirm `
    --onedir `
    --name LiveCaption `
    --distpath "$desktopFolder" `
    --hidden-import=faster_whisper `
    --hidden-import=ctranslate2 `
    --hidden-import=transformers `
    --exclude-module pandas `
    --exclude-module scipy `
    --exclude-module matplotlib `
    --exclude-module IPython `
    --exclude-module jupyter `
    --exclude-module tensorflow `
    --exclude-module tensorboard `
    --exclude-module sklearn `
    --exclude-module PIL `
    --exclude-module cv2 `
    --exclude-module notebook `
    --exclude-module sphinx `
    --exclude-module safetensors `
    --exclude-module rich `
    --exclude-module typer `
    --exclude-module click `
    --exclude-module jinja2 `
    --add-data "$fasterWhisperAssets;faster_whisper\assets" `
    main.py

if (-not (Test-Path "$desktopPath\LiveCaption.exe")) {

    Write-Host ""
    Write-Host "Build Failed!"
    exit 1
}

Copy-Item `
    ".\config.json" `
    "$desktopPath\config.json" `
    -Force

Write-Host "Check 240 availability..."

if (Test-Path $publishPath) {

    Write-Host "Dispatch to 240 (exe/_internal/config.json only)..."

    robocopy `
        "$desktopPath\_internal" `
        "$publishPath\_internal" `
        /MIR `
        /R:1 `
        /W:1

    Copy-Item `
        "$desktopPath\LiveCaption.exe" `
        "$publishPath\LiveCaption.exe" `
        -Force

    Copy-Item `
        "$desktopPath\config.json" `
        "$publishPath\config.json" `
        -Force

    Write-Host ""
    Write-Host "Build Complete (dispatched to 240)"

} else {

    Write-Host "240 not reachable, skip dispatch."
    Write-Host ""
    Write-Host "Build Complete (local only, not dispatched to 240)"
}