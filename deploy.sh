#!/bin/bash
set -e

NAMESPACE="evaluacion-quinquenal"

echo "=== Desplegando Evaluación Quinquenal UASD-MESCyT ==="

echo "1. Creando namespace..."
kubectl apply -f k8s/00-namespace.yaml

echo "2. Aplicando secrets..."
kubectl apply -f k8s/01-secrets.yaml

echo "3. Desplegando PostgreSQL..."
kubectl apply -f k8s/02-postgres.yaml

echo "4. Esperando a que PostgreSQL esté listo..."
kubectl rollout status deployment/postgres -n $NAMESPACE --timeout=120s

echo "5. Desplegando Backend..."
kubectl apply -f k8s/03-backend.yaml

echo "6. Ejutando migraciones..."
kubectl wait --for=condition=ready pod -l app=backend -n $NAMESPACE --timeout=120s
MIGRATION_POD=$(kubectl get pods -n $NAMESPACE -l app=backend -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n $NAMESPACE $MIGRATION_POD -- python manage.py migrate --noinput
kubectl exec -n $NAMESPACE $MIGRATION_POD -- python manage.py collectstatic --noinput

echo "7. Desplegando Frontend..."
kubectl apply -f k8s/04-frontend.yaml

echo "8. Configurando Ingress..."
kubectl apply -f k8s/05-ingress.yaml

echo "=== Despliegue completado ==="
echo "Frontend: http://localhost"
echo "Backend API: http://localhost/api/"
