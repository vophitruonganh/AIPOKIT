# One-time setup for pokit-browser on Windows (PowerShell). Safe to run again.
# Installs Playwright and its Chromium into %USERPROFILE%\.po-kit\browser, then runs the doctor.
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$pk = if ($env:POKIT_HOME) { $env:POKIT_HOME } else { Join-Path $HOME '.po-kit' }
$deps = Join-Path $pk 'browser'
$ver = if ($env:POKIT_PW_VERSION) { $env:POKIT_PW_VERSION } else { '1.63.0' }
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node -or [int](node -p "process.versions.node.split('.')[0]") -lt 18) {
  if (Get-Command winget -ErrorAction SilentlyContinue) { winget install -e --id OpenJS.NodeJS.LTS; Write-Host 'Node.js installed. Open a new PowerShell window and run this script again.'; exit 1 }
  Write-Host 'Node.js 18 or newer is needed. Install the LTS from https://nodejs.org, then run this script again.'; exit 1
}
New-Item -ItemType Directory -Force -Path $deps | Out-Null
$pkg = Join-Path $deps 'package.json'
if (-not (Test-Path $pkg)) { '{"private":true,"name":"pokit-browser-deps"}' | Set-Content -Encoding UTF8 $pkg }
npm install --prefix "$deps" --no-audit --no-fund --loglevel=error "playwright@$ver"
node (Join-Path $deps 'node_modules\playwright\cli.js') install chromium
if ($LASTEXITCODE -ne 0) { Write-Host 'Chromium download failed (blocked network?). The runner will use the installed Google Chrome or Edge, in a separate profile.' }
node (Join-Path $here 'pokit-browser.mjs') doctor
Write-Host "Next: node `"$here\pokit-browser.mjs`" login --url https://your-app.example.com"
