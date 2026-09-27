param(
    [ValidateSet('docker', 'k8s')]
    [string]$mode = 'docker',
    [string]$kubeContext = 'docker-desktop',
    # Fuerza la build local de las imagenes en vez de usar las de GHCR.
    # Necesario despues de cambiar codigo: .\up.ps1 -Build
    [switch]$Build
)

$ErrorActionPreference = 'Stop'
$NAMESPACE = 'evaluacion-quinquenal'

function Test-Tool {
    param([string]$name, [string]$hint)
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "Falta '$name'. $hint"
    }
}

function Get-ConflictosDePuerto {
    # Devuelve los puertos publicados por el compose que ya estan ocupados por
    # algo que no es nuestro. En una PC nueva es la causa mas comun de que el
    # stack no levante (IIS, XAMPP, otro stack de Docker, un visor de DB...).
    $project = ((Split-Path $PSScriptRoot -Leaf) -replace '[^A-Za-z0-9_-]', '').ToLower()
    $cfg = docker compose config --format json | ConvertFrom-Json

    $conflictos = @()
    foreach ($svc in $cfg.services.PSObject.Properties) {
        foreach ($p in @($svc.Value.ports)) {
            if (-not $p.published) { continue }
            $puerto = [int]$p.published
            $escucha = Get-NetTCPConnection -State Listen -LocalPort $puerto -ErrorAction SilentlyContinue | Select-Object -First 1
            if (-not $escucha) { continue }

            $propietario = ''
            $nuestro = $false

            # Preguntarle a Docker quien tiene el puerto publicado es mas fiable
            # que mirar el proceso: en Docker Desktop con WSL2 el listener lo
            # tiene wslrelay.exe, no un proceso con "docker" en el nombre.
            $propietario = ((docker ps --filter "publish=$puerto" --format '{{.Names}}' 2>$null) -join ' ').Trim()
            if ($propietario) {
                $nuestro = $propietario -like "*$project*"
            }
            else {
                $proc = Get-Process -Id $escucha.OwningProcess -ErrorAction SilentlyContinue
                $propietario = if ($proc) { "el proceso $($proc.ProcessName) (PID $($escucha.OwningProcess))" } else { "un PID $($escucha.OwningProcess)" }
            }

            if (-not $nuestro) {
                $conflictos += [pscustomobject]@{
                    Servicio = $svc.Name
                    Puerto   = $puerto
                    Ocupado  = $propietario
                }
            }
        }
    }
    return $conflictos
}

function Wait-BackendHealth {
    $url = 'http://localhost:8000/health/'
    $deadline = (Get-Date).AddSeconds(120)
    do {
        try {
            $r = Invoke-WebRequest -Uri $url -TimeoutSec 3 -UseBasicParsing
            if ($r.StatusCode -eq 200) { return }
        }
        catch {}
        Write-Host '  esperando a que el backend responda...'
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $deadline)
    Write-Error "El backend no respondio en $url dentro de 120s."
}

Write-Host "=== Sistema de Evaluacion Quinquenal UASD-MESCyT (modo: $mode) ==="

if ($mode -eq 'docker') {
    Test-Tool docker 'Instala Docker Desktop y vuelve a correr el script.'

    Write-Host '1. Descargando imagenes base (postgres, redis)...'
    docker compose pull
    if ($LASTEXITCODE -ne 0) {
        Write-Host '  AVISO: alguna imagen base no se pudo descargar.'
        Write-Host '  Docker construira las que falten, pero conviene revisar la conexion.'
    }

    Write-Host '2. Levantando Postgres, Redis, Backend y Frontend...'
    $conflictos = Get-ConflictosDePuerto
    if ($conflictos) {
        Write-Host '  AVISO: hay puertos ocupados por otro programa:' -ForegroundColor Yellow
        foreach ($c in $conflictos) {
            Write-Host "    puerto $($c.Puerto) (servicio $($c.Servicio)) lo tiene: $($c.Ocupado)" -ForegroundColor Yellow
        }
        Write-Host '  Si el stack no levanta, cambia el puerto en docker-compose.yml, por ejemplo:'
        Write-Host '    ports: ["8080:80"]   en el servicio frontend' -ForegroundColor Yellow
        Write-Host '    ports: ["127.0.0.1:8081:8000"]   en el servicio backend' -ForegroundColor Yellow
    }
    if ($Build) {
        Write-Host '  -Build activo: reconstruyendo las imagenes en local.'
        docker compose up -d --build
    }
    else {
        docker compose up -d
    }
    if ($LASTEXITCODE -ne 0) { Write-Error 'docker compose up fallo.' }

    Write-Host '3. Esperando a que el backend este sano...'
    Wait-BackendHealth

    Write-Host '4. Asegurando permisos del volumen media/logs...'
    docker compose exec -u root -T backend chown -R appuser:appuser /app/media /app/logs | Out-Null

    Write-Host '5. Aplicando migraciones...'
    docker compose exec -T backend python manage.py migrate --noinput

    Write-Host '6. Recopilando archivos estaticos...'
    docker compose exec -T backend python manage.py collectstatic --noinput

    Write-Host '=== Despliegue local (docker) completado ==='
    Write-Host 'Frontend:     http://localhost'
    Write-Host 'Backend API:  http://localhost:8000/api/'
    Write-Host 'Docs API:     http://localhost:8000/api/docs/'
}
else {
    Test-Tool docker 'Instala Docker Desktop y vuelve a correr el script.'
    Test-Tool kubectl 'kubectl viene con Docker Desktop; reinstala y vuelve a correr.'

    $ctx = @(kubectl config get-contexts -o name 2>$null)
    if ($LASTEXITCODE -ne 0 -or $ctx -notcontains $kubeContext) {
        Write-Error "No hay un cluster '$kubeContext'. Activa Kubernetes en Docker Desktop (Settings > Kubernetes > Enable cluster), espera a que Docker se reinicie y vuelve a correr."
    }
    kubectl config use-context $kubeContext | Out-Null

    Write-Host '1. Construyendo imagenes backend y frontend...'
    docker build -t evaluacion-quinquenal/backend:local ./backend
    docker build -t evaluacion-quinquenal/frontend:local ./frontend/evaluacion-quinquenal-front

    Write-Host '2. Aplicando namespace y secrets...'
    kubectl apply -f k8s/00-namespace.yaml
    kubectl apply -f k8s/01-secrets.yaml

    Write-Host '3. Desplegando PostgreSQL y Redis...'
    kubectl apply -f k8s/02-postgres.yaml
    kubectl apply -f k8s/06-redis.yaml
    kubectl rollout status deployment/postgres -n $NAMESPACE --timeout=180s
    kubectl rollout status deployment/redis -n $NAMESPACE --timeout=120s

    Write-Host '4. Desplegando Backend (imagen local)...'
    $backendYaml = (Get-Content k8s/03-backend.yaml -Raw) -replace 'evaluacion-quinquenal/backend:latest', 'evaluacion-quinquenal/backend:local'
    $backendYaml | kubectl apply -f -
    kubectl rollout status deployment/backend -n $NAMESPACE --timeout=240s

    Write-Host '5. Ejecutando migraciones y estaticos...'
    kubectl wait --for=condition=ready pod -l app=backend -n $NAMESPACE --timeout=180s
    $POD = kubectl get pods -n $NAMESPACE -l app=backend -o jsonpath='{.items[0].metadata.name}'
    kubectl exec -n $NAMESPACE $POD -- python manage.py migrate --noinput
    kubectl exec -n $NAMESPACE $POD -- python manage.py collectstatic --noinput

    Write-Host '6. Desplegando Frontend (imagen local), Ingress y backups...'
    $frontendYaml = (Get-Content k8s/04-frontend.yaml -Raw) -replace 'evaluacion-quinquenal/frontend:latest', 'evaluacion-quinquenal/frontend:local'
    $frontendYaml | kubectl apply -f -
    kubectl apply -f k8s/05-ingress.yaml
    kubectl apply -f k8s/07-backup.yaml
    kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=240s

    Write-Host '=== Despliegue local (kubernetes) completado ==='
    kubectl get pods,svc,ingress -n $NAMESPACE
    Write-Host 'Frontend:    http://localhost'
    Write-Host 'Backend API: http://localhost/api/'
}