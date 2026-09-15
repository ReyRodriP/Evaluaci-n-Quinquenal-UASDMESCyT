from django.test import TestCase, override_settings
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_endpoint_returns_ok(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["components"]["database"], "ok")

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}})
    def test_cache_component_fails_with_dummy_cache(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["components"]["cache"], "error")
