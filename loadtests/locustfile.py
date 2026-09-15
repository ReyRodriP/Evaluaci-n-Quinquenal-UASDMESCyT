"""Test de carga para la API de Evaluacion Quinquenal UASD-MESCyT.

Uso (con 100+ usuarios concurrentes):
    pip install locust
    locust -f loadtests/locustfile.py --host http://localhost:8000 -u 100 -r 10 -t 5m
"""

from locust import HttpUser, between, task


class EvaluacionAPIUser(HttpUser):
    """Usuario simulado: obtiene tokens JWT y consulta endpoints frecuentes."""

    wait_time = between(1, 5)

    def on_start(self):
        response = self.client.post(
            "/api/login",
            json={
                "username": self.username,
                "password": self.password,
            },
        )
        data = response.json() if response.ok else {}
        self.access_token = data.get("access")
        if self.access_token:
            self.client.headers.update({"Authorization": f"Bearer {self.access_token}"})

    @task(30)
    def dashboard_resumen(self):
        self.client.get("/api/dashboard/resumen/")

    @task(20)
    def dashboard_avance(self):
        self.client.get("/api/dashboard/avance/")

    @task(15)
    def listar_facultades(self):
        self.client.get("/api/facultades/")

    @task(10)
    def listar_periodos(self):
        self.client.get("/api/periodos/")

    @task(10)
    def buscar(self):
        self.client.get("/api/search/", params={"q": "doc"})

    @task(5)
    def listar_notificaciones(self):
        self.client.get("/api/notificaciones/")

    @task(5)
    def reporte_general(self):
        self.client.get("/api/reportes/general/")

    @task(3)
    def perfil(self):
        self.client.get("/api/me")
