$ErrorActionPreference = 'Stop'

$workspaceLinux = '/mnt/d/xiao/Documents/ChatGPT/Π0'
wsl.exe -d openpi-ubuntu-22.04 -- bash "$workspaceLinux/scripts/verify_environment.sh"
if ($LASTEXITCODE -ne 0) {
    throw "openpi environment verification failed with exit code $LASTEXITCODE"
}

