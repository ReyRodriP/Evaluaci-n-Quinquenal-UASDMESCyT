<#
.SYNOPSIS
    Publica las imagenes de backend y frontend en GitHub Container Registry y
    las deja publicas, para que el equipo las descargue sin `docker login`.

.DESCRIPTION
    1. Valida el PAT antes de tocar nada: que exista, que tenga forma de token,
       que pertenezca a la cuenta propietaria del repo y que tenga permisos de
       escritura de paquetes. Si algo falla, dice exactamente cual.
    2. Autentica en ghcr.io (solo si hace falta).
    3. Construye las imagenes leyendo el contexto de docker-compose.yml, para
       que el nombre de la imagen no dependa de IMAGE_* del .env local.
    4. Etiqueta con `latest`, con la rama y con el commit (marca `-dirty` si
       hay cambios sin commitear, porque ese SHA no describe la imagen).
    5. Sube las imagenes.
    6. Cambia la visibilidad de los dos paquetes a Public.
    7. Verifica la descarga anonima (sin credenciales) de las dos imagenes.

.EXAMPLE
    $env:GHCR_TOKEN = 'ghp_...'
    .\publicar-imagenes.ps1
    Publica, deja los paquetes publicos y comprueba el pull anonimo.

.EXAMPLE
    .\publicar-imagenes.ps1 -SkipBuild
    Reutiliza las imagenes ya construidas en local (no recompila Angular).

.EXAMPLE
    .\publicar-imagenes.ps1 -SkipVisibility
    Solo sube las imagenes, sin tocar la visibilidad (util para reintentos).
#>
param(
    [string]$Registry = 'ghcr.io',
    [string]$Owner = 'ReyRodriP',
    [string]$Package = 'evaluacion-n-quinquenal-uasdmescyt',
    [string]$Tag = 'latest',
    # Reutiliza las imagenes locales en vez de reconstruirlas.
    [switch]$SkipBuild,
    # No modifica la visibilidad de los paquetes.
    [switch]$SkipVisibility
)

$ErrorActionPreference = 'Stop'

# GHCR exige minusculas en la ruta de la imagen.
$ns = $Owner.ToLower()
$path = "$Registry/$ns/$Package"
$services = @('backend', 'frontend')

function Write-Step {
    param([string]$Message)
    Write-Host ''
    Write-Host "==> $Message"
}

function Get-GitInfo {
    # Devuelve rama, sha corto y si el arbol tiene cambios sin commitear.
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{ Branch = 'local'; Sha = 'local'; Dirty = $false }
    }
    $branch = (git rev-parse --abbrev-ref HEAD 2>$null)
    $sha = (git rev-parse --short HEAD 2>$null)
    $dirty = [bool](git status --porcelain 2>$null)
    if (-not $branch) { $branch = 'local' }
    if (-not $sha) { $sha = 'local' }
    return [pscustomobject]@{ Branch = $branch; Sha = $sha; Dirty = $dirty }
}

function Test-Pat {
    # Valida el PAT contra la API de GitHub y devuelve identidad y scopes.
    # No lanza excepcion: devuelve un objeto con Ok=$false y el motivo.
    param([string]$Token)
    $result = [pscustomobject]@{ Ok = $false; Login = ''; Scopes = ''; FineGrained = $false; Error = '' }

    if (-not $Token) { $result.Error = 'no se indico ningun token'; return $result }

    # Los tokens de GitHub empiezan por ghp_ (classic), github_pat_ (fine-grained)
    # o gho_/ghu_ (OAuth / app). Si no cumple, casi siempre es un token mal pegado.
    if ($Token -notmatch '^(ghp_|gho_|ghu_|ghs_|github_pat_)[A-Za-z0-9_]+$') {
        $result.Error = "el valor no tiene forma de token de GitHub (empieza por '$(if ($Token.Length -ge 4) { $Token.Substring(0, 4) } else { $Token }))"
        return $result
    }

    $headers = @{
        Authorization          = "Bearer $Token"
        Accept                 = 'application/vnd.github+json'
        'X-GitHub-Api-Version' = '2022-11-28'
    }
    try {
        $r = Invoke-WebRequest -Uri 'https://api.github.com/user' -Headers $headers -TimeoutSec 30 -UseBasicParsing
        $result.Login = ($r.Content | ConvertFrom-Json).login
        $scopes = $r.Headers['X-OAuth-Scopes']
        if ($scopes) { $result.Scopes = $scopes } else { $result.FineGrained = $true }
        $result.Ok = $true
    }
    catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        $result.Error = if ($code -eq 401) { 'GitHub lo rechazo (401): token invalido, expirado o revocado' }
        elseif ($code -eq 403) { 'GitHub lo rechazo (403): el token no tiene permiso para leerse a si mismo' }
        else { "GitHub no respondio ($code): $($_.Exception.Message)" }
    }
    return $result
}

function Get-BuildContext {
    # Lee del compose el contexto y el Dockerfile de cada servicio, para no
    # depender de las variables IMAGE_* del .env local.
    $cfg = docker compose config --format json | ConvertFrom-Json
    $out = @{}
    foreach ($s in $services) {
        $b = $cfg.services.$s.build
        if (-not $b) { Write-Error "El servicio '$s' no tiene seccion build en docker-compose.yml." }
        $ctx = $b.context
        $df = if ([System.IO.Path]::IsPathRooted($b.dockerfile)) { $b.dockerfile } else { Join-Path $ctx $b.dockerfile }
        $out[$s] = @{ Context = $ctx; Dockerfile = $df }
    }
    return $out
}

function Invoke-Anonimo {
    # Comprueba si una imagen se puede descargar SIN credenciales.
    # Devuelve $true / $false y no lanza excepcion.
    param([string]$Repo, [string]$Tag)
    try {
        $token = (Invoke-RestMethod -Uri "https://$Registry/token?scope=repository:$Repo`:pull&service=$Registry" -TimeoutSec 30).token
        if (-not $token) { return $false }
        $headers = @{
            Authorization = "Bearer $token"
            # GHCR responde 404 si el Accept no incluye el media type exacto
            # de la imagen (OCI manifest, OCI index, Docker v2 o Docker list).
            Accept        = 'application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.docker.distribution.manifest.list.v2+json'
        }
        $r = Invoke-WebRequest -Uri "https://$Registry/v2/$Repo/manifests/$Tag" -Headers $headers -TimeoutSec 30 -UseBasicParsing
        return ($r.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

Write-Host "=== Publicando imagenes en $path ==="
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'Falta Docker. Instala Docker Desktop y vuelve a correr el script.'
}

# --- 1. Validacion del PAT --------------------------------------------------
Write-Step '1. Validando el token...'
$token = if ($env:GHCR_TOKEN) { $env:GHCR_TOKEN.Trim() } else { '' }
if (-not $token) {
    Write-Host '  Falta la variable GHCR_TOKEN con un PAT que tenga el scope write:packages.'
    Write-Host '  Crear token (de la cuenta ' $Owner '): https://github.com/settings/tokens'
    Write-Host "  Despues:  `$env:GHCR_TOKEN = 'ghp_...'"
    Write-Error 'Sin token no se puede publicar.'
}

$pat = Test-Pat -Token $token
if (-not $pat.Ok) {
    Write-Host '  El token no sirve:' -ForegroundColor Red
    Write-Host "    $Owner / $Registry -> $($pat.Error)"
    Write-Host '  Comprueba que:'
    Write-Host '    1. Lo copiaste completo, sin comillas ni espacios al final.'
    Write-Host '    2. No esta expirado ni revocado.'
    Write-Host "    3. Es un PAT de la cuenta $Owner (Settings > Developer settings)."
    Write-Error 'Token no valido.'
}
if ($pat.Login -ine $Owner) {
    Write-Host "  El token pertenece a '$($pat.Login)', pero el namespace $path" -ForegroundColor Red
    Write-Host "  pertenece a '$Owner'." -ForegroundColor Red
    Write-Host '  En GHCR cada usuario publica en su propio namespace: un token de otra cuenta'
    Write-Host "  no puede subir a $path aunque tenga permisos sobre el repositorio."
    Write-Host "  Genera el PAT desde la cuenta ${Owner}: https://github.com/settings/tokens"
    Write-Error 'Token de otra cuenta.'
}
if ($pat.FineGrained) {
    Write-Host "  Token de alcance fino de '$($pat.Login)' (no se puede verificar el permiso de"
    Write-Host '  paquetes por API; si el push falla, usa un token classic con write:packages).'
}
elseif ($pat.Scopes -notmatch 'write:packages') {
    Write-Host "  Al token de '$($pat.Login)' le falta el scope write:packages." -ForegroundColor Red
    Write-Host "  Scopes actuales: $($pat.Scopes)"
    Write-Host '  Edita el token en https://github.com/settings/tokens y marca write:packages.'
    Write-Error 'Token sin permiso de escritura de paquetes.'
}
else {
    Write-Host "  Token de '$($pat.Login)' con scope write:packages. OK"
}

# --- 2. Autenticacion en el registry ----------------------------------------
Write-Step '2. Autenticando en el registry...'
$token | docker login $Registry --username $pat.Login --password-stdin | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host '  docker login fallo aunque el token sea valido para la API de GitHub.' -ForegroundColor Red
    Write-Host '  Causas habituales: Docker Desktop detenido, proxy/VPN, o un docker'
    Write-Host "  credential helper roto. Prueba:  docker logout $Registry   y vuelve a correr."
    Write-Error 'No se pudo autenticar en el registry.'
}
Write-Host "  Conectado como '$($pat.Login)' en $Registry"

# --- 3. Build ---------------------------------------------------------------
$contexts = Get-BuildContext
if ($SkipBuild) {
    Write-Step '3. Reutilizando las imagenes locales (-SkipBuild)'
    foreach ($s in $services) {
        docker image inspect "$path/$s`:$Tag" *> $null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  No existe la imagen local $path/$s`:$Tag." -ForegroundColor Red
            Write-Host "  Contexto de build segun compose: $($contexts[$s].Context)"
            Write-Host '  Quita -SkipBuild para construirla.'
            Write-Error 'Falta la imagen local.'
        }
        Write-Host "  $s`:$Tag ya existe en local"
    }
}
else {
    Write-Step '3. Construyendo imagenes (Angular puede tardar 2-4 min)...'
    foreach ($s in $services) {
        $c = $contexts[$s]
        Write-Host "  $s <- contexto $($c.Context), dockerfile $($c.Dockerfile)"
        docker build -t "$path/$s`:$Tag" -f $c.Dockerfile $c.Context
        if ($LASTEXITCODE -ne 0) { Write-Error "Falló el build de $s." }
    }
}

# --- 4. Etiquetas -----------------------------------------------------------
$git = Get-GitInfo
$shaTag = if ($git.Dirty) { "$($git.Sha)-dirty" } else { $git.Sha }
$branchTag = ($git.Branch -replace '[^A-Za-z0-9._-]', '-').ToLower()
$tags = @($Tag, $branchTag, $shaTag) | Select-Object -Unique

Write-Step "4. Etiquetando (rama '$($git.Branch)', commit $($git.Sha))"
if ($git.Dirty) {
    Write-Host '  AVISO: hay cambios sin commitear, por eso el tag del commit lleva "-dirty".' -ForegroundColor Yellow
    Write-Host '  Ese commit NO describe esta imagen. Commitea si quieres trazabilidad.' -ForegroundColor Yellow
}
foreach ($s in $services) {
    foreach ($t in $tags) {
        if ($t -ne $Tag) { docker tag "$path/$s`:$Tag" "$path/$s`:$t" }
    }
    Write-Host "  $s -> $($tags -join ', ')"
}

if ($git.Branch -ine 'main' -and $git.Branch -ine 'master') {
    Write-Host ''
    Write-Host "  AVISO: estas publicando el codigo de la rama '$($git.Branch)', no de main." -ForegroundColor Yellow
    Write-Host '  El workflow de CI tambien escribe la etiqueta `latest` al fusionar a main,' -ForegroundColor Yellow
    Write-Host '  asi que esa fusion cambiara lo que el equipo descarga. Para publicar sin' -ForegroundColor Yellow
    Write-Host "  tocar '$Tag', usa:  .\publicar-imagenes.ps1 -Tag $($git.Sha)" -ForegroundColor Yellow
}

# --- 5. Push ----------------------------------------------------------------
Write-Step "5. Subiendo imagenes a $path ($($tags.Count) tags por servicio)..."
foreach ($s in $services) {
    foreach ($t in $tags) {
        Write-Host "  $s`:$t"
        docker push "$path/$s`:$t" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Fallo al subir $s`:$t" -ForegroundColor Red
            Write-Host '  "denied" = el PAT no pudo escribir en el namespace (revisa el paso 1).'
            Write-Host '  "no space" / "quota" = la cuenta se quedo sin espacio en GHCR.'
            Write-Error 'Push fallido.'
        }

    }
}

# --- 6. Visibilidad publica -------------------------------------------------
if ($SkipVisibility) {
    Write-Step '6. Visibilidad omitida (-SkipVisibility)'
}
else {
    Write-Step '6. Cambiando la visibilidad de los paquetes a Public...'
    $headers = @{
        Authorization          = "Bearer $token"
        Accept                 = 'application/vnd.github+json'
        'X-GitHub-Api-Version' = '2022-11-28'
    }
    foreach ($s in $services) {
        $uri = "https://api.github.com/users/$ns/packages/container/$s"
        try {
            $r = Invoke-RestMethod -Method Patch -Uri $uri -Headers $headers -Body (@{ visibility = 'public' } | ConvertTo-Json) -ContentType 'application/json' -TimeoutSec 30
            Write-Host "  $s -> $($r.visibility)"
        }
        catch {
            Write-Host "  $s -> no se pudo cambiar por API: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "  Hazlo manual: https://github.com/users/$ns/packages/container/$s/settings" -ForegroundColor Yellow
        }
    }
}

# --- 7. Verificacion anonima ------------------------------------------------
Write-Step '7. Verificando descarga sin credenciales...'
$todo = $true
foreach ($s in $services) {
    $ok = Invoke-Anonimo -Repo "$ns/$Package/$s" -Tag $Tag
    if ($ok) { Write-Host "  $s`:$Tag -> OK (publico, se puede hacer pull sin login)" -ForegroundColor Green }
    else { Write-Host "  $s`:$Tag -> todavia NO se puede descargar sin credenciales" -ForegroundColor Yellow; $todo = $false }
}

Write-Host ''
if ($todo) {
    Write-Host '=== PUBLICADO ==='
    Write-Host "Imagenes: $path/backend:$Tag y $path/frontend:$Tag"
    Write-Host "Tambien: $path/backend:$shaTag, $path/frontend:$shaTag"
    Write-Host ''
    Write-Host 'El equipo puede levantarlas con:'
    Write-Host '  git clone <repo>'
    Write-Host '  cd <repo>'
    Write-Host '  .\setup-todo.ps1'
}
else {
    Write-Host '=== PUBLICADO CON AVISOS ==='
    Write-Host 'Las imagenes estan subidas, pero la descarga anonima falla.'
    Write-Host "Revisa la visibilidad en https://github.com/users/$ns/packages"
}
