$desktopPath = "C:\Users\PC-103\Desktop\LiveCaption"
$publishPath = "\\192.168.0.240\project\Ken_Lin\LiveCaption"

Write-Host "Check LiveCaption..."

$proc = Get-Process -Name "LiveCaption" -ErrorAction SilentlyContinue

if ($proc) {

    Write-Host "LiveCaption is running!"
    Write-Host "Please close LiveCaption.exe first."

    exit 1
}

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
    --distpath "C:\Users\PC-103\Desktop" `
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
    --add-data "C:\Users\PC-103\AppData\Local\Programs\Python\Python312\Lib\site-packages\faster_whisper\assets;faster_whisper\assets" `
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