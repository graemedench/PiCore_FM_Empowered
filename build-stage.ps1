# Recreate the staged prototype from pinned upstream sources via HTTPS.
# Run from the project root with Git and tar installed. No device changes.
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$buildRoot = Join-Path $projectRoot 'build'
if (Test-Path -LiteralPath $buildRoot) {
    throw 'Build directory already exists. Use a fresh checkout to preserve existing work.'
}
New-Item -ItemType Directory -Path $buildRoot | Out-Null
$sableRoot = Join-Path $buildRoot 'sable'
$patchRoot = Join-Path $buildRoot 'empowered'
git clone https://github.com/theshepherdmatt/sable.git $sableRoot
if ($LASTEXITCODE) { throw 'Sable clone failed' }
git -C $sableRoot checkout 3670e503db8124de5890a6df1dc1b68b95d392a6
if ($LASTEXITCODE) { throw 'Pinned Sable revision unavailable' }
git clone https://github.com/graemedench/quadify_empowered.git $patchRoot
if ($LASTEXITCODE) { throw 'Empowered clone failed' }
git -C $patchRoot checkout ed3d9417b1b18fdd13a83a3dd5b65505c7bef0c7
if ($LASTEXITCODE) { throw 'Pinned Empowered revision unavailable' }
git -C $sableRoot apply (Join-Path $patchRoot 'patches/sable-empowered.patch')
if ($LASTEXITCODE) { throw 'Upstream patch failed' }
Copy-Item -LiteralPath (Join-Path $projectRoot 'overlay/sable/pcp') -Destination (Join-Path $sableRoot 'src/sable/pcp') -Recurse
Copy-Item -Path (Join-Path $projectRoot 'tests/*.py') -Destination $sableRoot
Copy-Item -Path (Join-Path $projectRoot 'tools/*.py') -Destination $sableRoot
Copy-Item -LiteralPath (Join-Path $projectRoot 'stage-start.sh') -Destination $sableRoot
Copy-Item -LiteralPath (Join-Path $projectRoot 'receiver-hook.sh') -Destination $sableRoot
Copy-Item -LiteralPath (Join-Path $projectRoot 'receiver-levels.sh') -Destination $sableRoot
tar --exclude=__pycache__ -czf (Join-Path $projectRoot 'sable-pcp-stage.tar.gz') -C $sableRoot src assets config check_live.py check_transport.py check_buttons.py check_stop_resume.py check_levels_screen.py check_power.py check_receiver_levels.py enable-visualizer.py save-prototype-startup.py setup-native-receivers.py setup-receiver-levels.py setup-native-wifi.py install-bbc-sounds.py install-playhls.py receiver-hook.sh receiver-levels.sh stage-start.sh
if ($LASTEXITCODE) { throw 'Archive creation failed' }
Write-Host 'Staged archive created. See STAGING.md before deployment.'
