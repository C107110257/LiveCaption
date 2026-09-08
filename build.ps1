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

Write-Host "Build..."

pyinstaller `
    --noconfirm `
    --onedir `
    --name LiveCaption `
    --distpath "C:\Users\PC-103\Desktop" `
    --hidden-import=faster_whisper `
    --hidden-import=ctranslate2 `
    --hidden-import=transformers `
    --hidden-import=torch `
    --exclude-module pandas `
    --exclude-module scipy `
    --exclude-module matplotlib `
    --exclude-module IPython `
    --exclude-module jupyter `
    --add-data "C:\Users\PC-103\AppData\Local\Programs\Python\Python312\Lib\site-packages\faster_whisper\assets;faster_whisper\assets" `
    main.py

if (-not (Test-Path "$desktopPath\LiveCaption.exe")) {

    Write-Host ""
    Write-Host "Build Failed!"
    exit 1
}

Write-Host "Dispatch to 240..."

robocopy `
    $desktopPath `
    $publishPath `
    /MIR `
    /R:1 `
    /W:1

Write-Host ""
Write-Host "Build Complete"