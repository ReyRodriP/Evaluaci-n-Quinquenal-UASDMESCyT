param(
    [string]$Mode = 'docker',
    [string]$Username = 'mrPopoMaster',
    [string]$Email = 'popomrMaster001@gmail.com',
    [string]$Password = '12345678'
)

$ErrorActionPreference = 'Stop'
$NAMESPACE = 'evaluacion-quinquenal'

if ($Mode -eq 'k8s') {
    $ctx = @(kubectl config get-contexts -o name 2>$null)
    if ($LASTEXITCODE -ne 0 -or $ctx -notcontains 'docker-desktop') {
        Write-Error "No hay cluster docker-desktop. Usa -Mode docker o activa Kubernetes en Docker Desktop."
    }
    $POD = kubectl get pods -n $NAMESPACE -l app=backend -o jsonpath='{.items[0].metadata.name}'
    if (-not $POD) { Write-Error "No hay pod backend en el namespace $NAMESPACE. Corre primero .\up.ps1 -mode k8s." }
    Write-Host "Ejecutando en el pod backend ($POD)..."
    kubectl exec -n $NAMESPACE $POD -- python manage.py crear_superusuario --username "$Username" --email "$Email" --password "$Password"
}
else {
    Write-Host "Ejecutando en el contenedor backend..."
    docker compose exec -T backend python manage.py crear_superusuario --username "$Username" --email "$Email" --password "$Password"
}