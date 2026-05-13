# Copy IoT certificates from backend/certs to firmware/data/certs
# Run from project root: .\medai-cabinet\firmware\copy_certs.ps1

$src  = "medai-cabinet\backend\certs"
$dest = "medai-cabinet\firmware\data\certs"

New-Item -ItemType Directory -Force -Path $dest | Out-Null

# Copy device cert and key
Copy-Item "$src\medai-cabinet-device.cert.pem"    "$dest\" -Force
Copy-Item "$src\medai-cabinet-device.private.key" "$dest\" -Force

# Download Amazon Root CA if not present
$caPath = "$dest\AmazonRootCA1.pem"
if (-not (Test-Path $caPath)) {
    Write-Host "Downloading AmazonRootCA1.pem..."
    Invoke-WebRequest -Uri "https://www.amazontrust.com/repository/AmazonRootCA1.pem" -OutFile $caPath
}

Write-Host "Certificates copied to $dest"
Write-Host ""
Write-Host "Next: cd medai-cabinet\firmware && pio run --target uploadfs"
