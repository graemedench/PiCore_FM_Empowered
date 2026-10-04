$ErrorActionPreference = 'Stop'
$bundle = Join-Path $PSScriptRoot 'installer-bundle'
if (Test-Path -LiteralPath $bundle) { throw 'Use a fresh bundle directory; existing bundle preserved.' }
New-Item -ItemType Directory -Path $bundle | Out-Null
foreach ($name in @('sable-pcp-stage.tar.gz', 'requirements-lock.txt', 'INSTALL.md')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $bundle
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'installer/install.py') -Destination $bundle
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'recovery-panel') -Destination $bundle -Recurse
$hash = (Get-FileHash (Join-Path $bundle 'sable-pcp-stage.tar.gz') -Algorithm SHA256).Hash.ToLower()
[IO.File]::WriteAllText((Join-Path $bundle 'sable-pcp-stage.tar.gz.sha256'), "$hash  sable-pcp-stage.tar.gz`n")
tar -czf (Join-Path $PSScriptRoot 'fm4-installer.tar.gz') -C $bundle .
if ($LASTEXITCODE) { throw 'Installer packaging failed' }
Write-Host 'Installer bundle built. See INSTALL.md; fresh SSD validation remains required.'
