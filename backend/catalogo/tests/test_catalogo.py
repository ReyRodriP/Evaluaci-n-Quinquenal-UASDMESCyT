from django.test import TestCase
from django.db import IntegrityError
from catalogo import models


class CatalogoModelTests(TestCase):
    def setUp(self):
        self.v1 = models.VersionMarcoEvaluacion.objects.create(nombre='EQ-SIDACES 2026', slug='eq-sidaces-2026', activo=True)
        self.v2 = models.VersionMarcoEvaluacion.objects.create(nombre='EQ-SIDACES 2025', slug='eq-sidaces-2025', activo=False)

    def test_version_unica_activa(self):
        with self.assertRaises(IntegrityError):
            models.VersionMarcoEvaluacion.objects.create(nombre='Otra', slug='otra', activo=True)

    def test_dos_versiones_coexisten(self):
        self.assertTrue(self.v1.activo)
        self.assertFalse(self.v2.activo)
        self.assertEqual(models.VersionMarcoEvaluacion.objects.count(), 2)

    def test_jerarquia_unicidad_por_version(self):
        dim = models.Dimension.objects.create(version_marco=self.v1, codigo='I', nombre='Gestión', orden=1)
        comp = models.Componente.objects.create(version_marco=self.v1, dimension=dim, codigo='1.1', nombre='Comp', orden=1, codigo_completo='1.1')
        cmarco = models.CriterioMarco.objects.create(version_marco=self.v1, componente=comp, codigo='1.1.1', nombre='Criterio', orden=1, codigo_completo='1.1.1')
        est = models.Estandar.objects.create(version_marco=self.v1, criterio_marco=cmarco, codigo='1.1.1.1', redaccion='Std', orden=1, codigo_completo='1.1.1.1')
        ind = models.IndicadorMarco.objects.create(version_marco=self.v1, estandar=est, codigo='1.1.1.1.1', redaccion_oficial='Ind', orden=1, codigo_completo='1.1.1.1.1')
        evid = models.EvidenciaIndicativa.objects.create(version_marco=self.v1, indicador_marco=ind, codigo='1.1.1.1.1.1', descripcion='Evid', orden=1, codigo_completo='1.1.1.1.1.1')
        self.assertEqual(evid.codigo_completo, '1.1.1.1.1.1')
        self.assertEqual(ind.estandar.codigo_completo, '1.1.1.1')
        self.assertEqual(evid.indicador_marco.estandar.criterio_marco.componente.dimension.codigo, 'I')

    def test_unicidad_codigo_completo_por_version(self):
        dim = models.Dimension.objects.create(version_marco=self.v1, codigo='II', nombre='Académico', orden=2)
        comp = models.Componente.objects.create(version_marco=self.v1, dimension=dim, codigo='2.1', nombre='Comp', orden=1, codigo_completo='2.1')
        with self.assertRaises(IntegrityError):
            models.Componente.objects.create(version_marco=self.v1, dimension=dim, codigo='2.1b', nombre='Otro', orden=2, codigo_completo='2.1')

    def test_no_hay_dos_versiones_activas(self):
        self.assertTrue(self.v1.activo)
        with self.assertRaises(IntegrityError):
            models.VersionMarcoEvaluacion.objects.create(nombre='X', slug='x', activo=True)

