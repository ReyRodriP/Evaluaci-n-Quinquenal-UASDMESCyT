param(
    [ValidateSet('docker', 'k8s')]
    [string]$mode = 'docker',
    [string]$kubeContext = 'docker-desktop'
)

$ErrorActionPreference = 'Stop'
$NAMESPACE = 'evaluacion-quinquenal'

function Test-Tool {
    param([string]$name, [string]$hint)
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "Falta '$name'. $hint"
    }
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

    Write-Host '1. Construyendo y levantando Postgres, Redis, Backend y Frontend...'
    docker compose up -d --build

    Write-Host '2. Esperando a que el backend este sano...'
    Wait-BackendHealth

    Write-Host '3. Aplicando migraciones...'
    docker compose exec -T backend python manage.py migrate --noinput

    Write-Host '4. Recopilando archivos estaticos...'
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