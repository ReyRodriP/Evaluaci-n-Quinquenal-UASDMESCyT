param(
    [ValidateSet('docker', 'k8s')]
    [string]$Mode = 'docker',
    [string]$Username = 'mrPopoMaster',
    [string]$Email = 'popomrMaster001@gmail.com',
    [switch]$Git
)

$ErrorActionPreference = 'Stop'

function New-Password {
    $sets = @('abcdefghijkmnopqrstuvwxyz', 'ABCDEFGHJKLMNPQRSTUVWXYZ', '23456789', '!@$%^&*_-.')
    $list = @()
    foreach ($s in $sets) { $list += $s[(Get-Random -Maximum $s.Length)] }
    $all = $sets -join ''
    1..12 | ForEach-Object { $list += $all[(Get-Random -Maximum $all.Length)] }
    return (($list | Sort-Object { Get-Random }) -join '')
}

function Get-SuperuserPassword {
    $envFile = Join-Path $PSScriptRoot '.env'
    if (Test-Path $envFile) {
        $line = Get-Content $envFile | Where-Object { $_ -match '^SUPERUSER_PASSWORD=' } | Select-Object -First 1
        if ($line) { return ($line -split '=', 2)[1] }
    }
    $nueva = New-Password
    Add-Content -Path $envFile -Value "SUPERUSER_PASSWORD=$nueva"
    return $nueva
}

Write-Host "=== SETUP AUTOMATICO: Evaluacion Quinquenal UASD-MESCyT (modo: $Mode) ==="

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'Falta Docker. Instala Docker Desktop y vuelve a correr el script.'
}

$SUPERUSER_PASSWORD = Get-SuperuserPassword

Write-Host ""
Write-Host "1. Desplegando el proyecto ($Mode)..."
& (Join-Path $PSScriptRoot 'up.ps1') -mode $Mode
if ($LASTEXITCODE -ne 0) { Write-Error 'El despliegue fallo.' }

Write-Host ""
Write-Host "2. Creando/actualizando el superusuario '$Username'..."
& (Join-Path $PSScriptRoot 'crear_superusuario.ps1') -Mode $Mode -Username $Username -Email $Email -Password $SUPERUSER_PASSWORD
if ($LASTEXITCODE -ne 0) { Write-Error 'No se pudo crear el superusuario.' }

Write-Host ""
Write-Host "3. Verificando que todo responda..."
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $h = Invoke-WebRequest -Uri 'http://localhost:8000/health/' -UseBasicParsing -TimeoutSec 5
        if ($h.StatusCode -eq 200) { $ok = $true; break }
    } catch {}
    Start-Sleep -Seconds 2
}
if (-not $ok) { Write-Error 'El backend no respondio a /health/ tras el despliegue.' }

$frontStatus = (Invoke-WebRequest -Uri 'http://localhost' -UseBasicParsing -TimeoutSec 10).StatusCode
$body = @{ username = $Username; password = $SUPERUSER_PASSWORD } | ConvertTo-Json
$login = Invoke-RestMethod -Uri 'http://localhost:8000/api/login' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 15
if (-not $login.access) { Write-Error 'El login de verificacion fallo.' }

Write-Host ""
Write-Host "=== SISTEMA LISTO Y FUNCIONANDO ==="
Write-Host "Frontend:   http://localhost"
Write-Host "Backend:    http://localhost:8000/api/"
Write-Host "Docs API:   http://localhost:8000/api/docs/"
Write-Host "Salud:      http://localhost:8000/health/ (estado $($h.StatusCode), frontend $frontStatus)"
Write-Host ""
Write-Host "Credenciales de acceso:"
Write-Host "  Usuario:   $Username"
Write-Host "  Password:  $SUPERUSER_PASSWORD"
Write-Host "  (guardada en .env como SUPERUSER_PASSWORD)"

if ($Git) {
    Write-Host ""
    Write-Host "4. Actualizando git..."
    git add -A
    git commit -m "chore: despliegue automatico $(Get-Date -Format 'yyyy-MM-dd HH:mm')" --allow-empty
    git push
    Write-Host "  Git actualizado."
}