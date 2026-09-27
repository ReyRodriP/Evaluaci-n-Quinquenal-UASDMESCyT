<#
.SYNOPSIS
    Prepara el entorno de desarrollo local de Evaluacion Quinquenal UASD-MESCyT.

.DESCRIPTION
    Todo en un solo comando, en orden:
      1. Crea .env a partir de .env.dev (si no existe) con claves aleatorias.
      2. Descarga las imagenes de GHCR y levanta el stack (up.ps1).
      3. Sincroniza roles y permisos.
      4. Carga datos iniciales (facultades, departamentos, periodos, criterios).
      5. Crea o actualiza el superusuario de desarrollo.
      6. Verifica que el frontend y el login respondan.

.EXAMPLE
    .\setup-todo.ps1
    Usa .env si existe; si no, lo crea desde .env.dev.

.EXAMPLE
    .\setup-todo.ps1 -Username juan -Email juan@uased.local
    Sobrescribe el usuario del superusuario de desarrollo.

.EXAMPLE
    .\setup-todo.ps1 -Build
    Reconstruye las imagenes en local en vez de descargarlas de GHCR.
#>
param(
    [ValidateSet('docker', 'k8s')]
    [string]$Mode = 'docker',
    [string]$Username,
    [string]$Email,
    [string]$Password,
    # Reconstruye las imagenes localmente en vez de usar las de GHCR.
    [switch]$Build
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$envFile = Join-Path $root '.env'
$envDev = Join-Path $root '.env.dev'
$NAMESPACE = 'evaluacion-quinquenal'

function New-Password {
    $sets = @('abcdefghijkmnopqrstuvwxyz', 'ABCDEFGHJKLMNPQRSTUVWXYZ', '23456789', '!@$%^&*_-.')
    $list = @()
    foreach ($s in $sets) { $list += $s[(Get-Random -Maximum $s.Length)] }
    $all = $sets -join ''
    1..20 | ForEach-Object { $list += $all[(Get-Random -Maximum $all.Length)] }
    return (($list | Sort-Object { Get-Random }) -join '')
}

function New-SecretKey {
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#%+=_'
    $key = ''
    1..50 | ForEach-Object { $key += $chars[(Get-Random -Maximum $chars.Length)] }
    return $key
}

function Get-EnvValue {
    param([string]$Path, [string]$Key, [string]$Default = '')
    if (-not (Test-Path -LiteralPath $Path)) { return $Default }
    $pattern = '^\s*' + [regex]::Escape($Key) + '\s*='
    $line = Get-Content -LiteralPath $Path | Where-Object { $_ -match $pattern } | Select-Object -First 1
    if ($line) { return (($line -split '=', 2)[1]).Trim() }
    return $Default
}

function Set-EnvValue {
    # Reescribe el .env en UTF-8 sin BOM y con saltos LF (docker compose es picky).
    param([string]$Path, [string]$Key, [string]$Value)
    $pattern = '^\s*' + [regex]::Escape($Key) + '\s*='
    $lines = @(Get-Content -LiteralPath $Path)
    $found = $false
    $out = foreach ($line in $lines) {
        if ($line -match $pattern) { $found = $true; "$Key=$Value" } else { $line }
    }
    if (-not $found) { $out = @($out) + "$Key=$Value" }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, (($out -join "`n") + "`n"), $utf8NoBom)
}

function Initialize-EnvFile {
    if (Test-Path -LiteralPath $envFile) {
        Write-Host '  .env ya existe: se respeta tu configuracion actual.'
        Write-Host '  Si lo copiaste desde otro equipo o esta Sharing, borralo y vuelve a correr'
        Write-Host '  el script para generar uno propio (claves nuevas y superusuario propio).'
    }
    else {
        if (-not (Test-Path -LiteralPath $envDev)) {
            Write-Error "No existe .env ni la plantilla .env.dev. Restaura el repositorio con 'git pull'."
        }
        Copy-Item -LiteralPath $envDev -Destination $envFile
        Set-EnvValue -Path $envFile -Key 'SECRET_KEY' -Value (New-SecretKey)
        Set-EnvValue -Path $envFile -Key 'DB_PASSWORD' -Value (New-Password)
        Set-EnvValue -Path $envFile -Key 'REDIS_PASSWORD' -Value (New-Password)
        Write-Host '  .env creado desde .env.dev con SECRET_KEY, DB_PASSWORD y REDIS_PASSWORD aleatorios.'
        Write-Host '  (gitignored: no se sube al repositorio)'
    }

    if (-not (Get-EnvValue -Path $envFile -Key 'SUPERUSER_PASSWORD')) {
        Set-EnvValue -Path $envFile -Key 'SUPERUSER_PASSWORD' -Value (New-Password)
        Write-Host '  SUPERUSER_PASSWORD generado y guardado en .env'
    }
}

function Invoke-Manage {
    # Ejecuta "python manage.py <args>" en el backend, en modo docker o k8s.
    # Uso: Invoke-Manage @('seed')  /  Invoke-Manage @('migrate', '--noinput')
    param([string[]]$ManageArgs)
    if ($Mode -eq 'k8s') {
        $pod = kubectl get pods -n $NAMESPACE -l app=backend -o jsonpath='{.items[0].metadata.name}'
        if (-not $pod) { Write-Error "No hay pod backend en el namespace $NAMESPACE. Corre primero .\up.ps1 -mode k8s." }
        & kubectl exec -n $NAMESPACE $pod -- python manage.py @ManageArgs
    }
    else {
        & docker compose exec -T backend python manage.py @ManageArgs
    }
    if ($LASTEXITCODE -ne 0) { Write-Error "Fallo: python manage.py $($ManageArgs -join ' ')" }
}

function Wait-Frontend {
    $deadline = (Get-Date).AddSeconds(120)
    do {
        try {
            $r = Invoke-WebRequest -Uri 'http://localhost' -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { return $true }
        } catch {}
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $deadline)
    return $false
}

function Test-Login {
    param([string]$User, [string]$Pass)
    $body = @{ username = $User; password = $Pass } | ConvertTo-Json
    $login = Invoke-RestMethod -Uri 'http://localhost:8000/api/login' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 15
    return [bool]$login.access
}

Write-Host "=== SETUP DE DESARROLLO LOCAL: Evaluacion Quinquenal UASD-MESCyT (modo: $Mode) ==="

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'Falta Docker. Instala Docker Desktop y vuelve a correr el script.'
}
if ($Mode -eq 'k8s' -and -not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Error 'Falta kubectl. Viene con Docker Desktop; reinstala y vuelve a correr.'
}

Write-Host ''
Write-Host '1. Preparando el archivo .env...'
Initialize-EnvFile

$superuserUser = if ($Username) { $Username } else { Get-EnvValue -Path $envFile -Key 'SUPERUSER_USERNAME' 'admin' }
$superuserMail = if ($Email) { $Email } else { Get-EnvValue -Path $envFile -Key 'SUPERUSER_EMAIL' 'admin@uased.local' }
$superuserPass = if ($Password) { $Password } else { Get-EnvValue -Path $envFile -Key 'SUPERUSER_PASSWORD' }

if ($superuserPass.Length -lt 8) {
    $superuserPass = New-Password
    Set-EnvValue -Path $envFile -Key 'SUPERUSER_PASSWORD' -Value $superuserPass
    Write-Host '  La contrasena del superusuario era muy corta: se genero una nueva en .env'
}

Write-Host ''
Write-Host '2. Levantando el stack...'
$upArgs = @{ mode = $Mode }
if ($Build) { $upArgs['Build'] = $true }
& (Join-Path $root 'up.ps1') @upArgs
if ($LASTEXITCODE -ne 0) { Write-Error 'El despliegue fallo.' }

Write-Host ''
Write-Host '3. Sincronizando roles y permisos...'
Invoke-Manage @('sync_roles')

Write-Host ''
Write-Host '4. Cargando datos iniciales (facultades, departamentos, periodos, criterios)...'
Invoke-Manage @('seed')

Write-Host ''
Write-Host "5. Creando/actualizando el superusuario '$superuserUser'..."
Invoke-Manage @('crear_superusuario', '--username', $superuserUser, '--email', $superuserMail, '--password', $superuserPass)

Write-Host ''
Write-Host '6. Verificando que todo responda...'
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $h = Invoke-WebRequest -Uri 'http://localhost:8000/health/' -UseBasicParsing -TimeoutSec 5
        if ($h.StatusCode -eq 200) { $ok = $true; break }
    } catch {}
    Start-Sleep -Seconds 2
}
if (-not $ok) { Write-Error 'El backend no respondio a /health/ tras el despliegue.' }

$frontOk = Wait-Frontend
$loginOk = Test-Login -User $superuserUser -Pass $superuserPass

Write-Host ''
Write-Host '=== SISTEMA LISTO Y FUNCIONANDO ==='
Write-Host "Frontend:    http://localhost          $(if ($frontOk) { '(OK)' } else { '(sin respuesta)' })"
Write-Host "Backend API: http://localhost:8000/api/"
Write-Host "Docs API:    http://localhost:8000/api/docs/"
Write-Host "Salud:       http://localhost:8000/health/  (HTTP $($h.StatusCode))"
Write-Host ''
Write-Host 'Credenciales de desarrollo:'
Write-Host "  Usuario:   $superuserUser"
Write-Host "  Password:  $superuserPass"
Write-Host "  (guardada en .env como SUPERUSER_PASSWORD)"
if (-not $loginOk) { Write-Host "  AVISO: el login de verificacion fallo. Revisa los logs con: docker compose logs backend" }

Write-Host ''
Write-Host 'Comandos utiles:'
Write-Host '  .\up.ps1              # levantar / actualizar el stack'
Write-Host '  .\up.ps1 -Build       # reconstruir imagenes locales tras cambiar codigo'
Write-Host '  docker compose logs -f backend'
Write-Host '  docker compose down -v   # borrar stack y datos (empezar de cero)'
