"""
@file seed.py
@brief Comando de gestión para cargar datos iniciales del sistema.
@details Define el comando 'seed' que pobla la base de datos con
facultades, departamentos, períodos, criterios, roles y permisos
iniciales necesarios para el funcionamiento de la aplicación.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """@class Command
    @brief Comando de Django management para sembrar datos iniciales.
    @details Ejecuta una secuencia de métodos de carga que crean registros
    base para la organización, evaluación, roles y permisos del sistema.
    """

    help = "Carga los datos iniciales del sistema"

    def handle(self, *args, **kwargs):
        """@brief Método principal que orquesta la carga de datos iniciales.
        @param args Argumentos posicionales adicionales.
        @param kwargs Argumentos de palabra clave adicionales.
        """
        self.seed_facultades()
        self.seed_departamentos()
        self.seed_periodos()
        self.seed_criterios()

        self.seed_roles()
        self.seed_groups()

        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados correctamente."))

    def seed_facultades(self):
        """@brief Crea las facultades iniciales del sistema.
        @details Registra las 9 facultades de la universidad usando
        get_or_create para evitar duplicados.
        """
        from organization.models import Facultad

        facultades = [
            {
                "nombre": "Facultad de Humanidades",
                "descripcion": "Responsable de la formación académica e investigación en las áreas de humanidades, letras, filosofía, historia y disciplinas afines.",
            },
            {
                "nombre": "Facultad de Ciencias",
                "descripcion": "Desarrolla programas académicos e investigaciones en ciencias básicas como matemática, física, química, biología e informática.",
            },
            {
                "nombre": "Facultad de Ciencias Económicas y Sociales",
                "descripcion": "Forma profesionales en economía, administración, contabilidad, mercadeo, sociología y otras ciencias sociales.",
            },
            {
                "nombre": "Facultad de Ciencias Jurídicas y Políticas",
                "descripcion": "Promueve la formación de profesionales en derecho, ciencias políticas y áreas relacionadas con la administración de justicia.",
            },
            {
                "nombre": "Facultad de Ingeniería y Arquitectura",
                "descripcion": "Desarrolla la formación de ingenieros y arquitectos mediante programas académicos orientados a la innovación y el desarrollo tecnológico.",
            },
            {
                "nombre": "Facultad de Ciencias de la Salud",
                "descripcion": "Forma profesionales de la salud y fomenta la investigación en medicina, odontología, enfermería y disciplinas afines.",
            },
            {
                "nombre": "Facultad de Ciencias Agronómicas y Veterinarias",
                "descripcion": "Impulsa la formación e investigación en agricultura, producción animal, veterinaria y desarrollo sostenible.",
            },
            {
                "nombre": "Facultad de Artes",
                "descripcion": "Promueve la formación artística y cultural en áreas como música, teatro, danza, artes visuales y diseño.",
            },
            {
                "nombre": "Facultad de Ciencias de la Educación",
                "descripcion": "Forma profesionales de la educación y desarrolla investigaciones orientadas al mejoramiento de los procesos de enseñanza y aprendizaje.",
            },
        ]

        for facultad in facultades:
            Facultad.objects.get_or_create(nombre=facultad["nombre"], defaults={"descripcion": facultad["descripcion"]})

        self.stdout.write(self.style.SUCCESS("Facultades registradas correctamente."))

    def seed_departamentos(self):
        """@brief Crea los departamentos iniciales de la Facultad de Ciencias.
        @details Registra las 7 escuelas de la Facultad de Ciencias usando
        get_or_create para evitar duplicados.
        """
        from organization.models import Departamento, Facultad

        facultad_ciencias = Facultad.objects.get(nombre="Facultad de Ciencias")

        departamentos = [
            {
                "nombre": "Escuela de Biología",
                "descripcion": "Unidad académica dedicada a la formación e investigación en las ciencias biológicas.",
            },
            {
                "nombre": "Escuela de Física",
                "descripcion": "Unidad académica responsable de la enseñanza e investigación en física y sus aplicaciones.",
            },
            {
                "nombre": "Escuela de Geografía",
                "descripcion": "Unidad académica orientada al estudio del espacio geográfico, el medio ambiente y el ordenamiento territorial.",
            },
            {
                "nombre": "Escuela de Informática",
                "descripcion": "Unidad académica dedicada a la formación de profesionales en informática, desarrollo de software y tecnologías de la información.",
            },
            {
                "nombre": "Escuela de Matemáticas",
                "descripcion": "Unidad académica encargada de la formación e investigación en matemáticas puras y aplicadas.",
            },
            {
                "nombre": "Escuela de Microbiología y Parasitología",
                "descripcion": "Unidad académica especializada en el estudio de microorganismos, parásitos y su impacto en la salud y el medio ambiente.",
            },
            {
                "nombre": "Escuela de Química",
                "descripcion": "Unidad académica dedicada a la enseñanza e investigación en química y ciencias afines.",
            },
        ]

        for departamento in departamentos:
            Departamento.objects.get_or_create(
                nombre=departamento["nombre"],
                facultad=facultad_ciencias,
                defaults={"descripcion": departamento["descripcion"]},
            )

        self.stdout.write(self.style.SUCCESS("Departamentos de la Facultad de Ciencias registrados correctamente."))

    def seed_periodos(self):
        """@brief Crea los períodos de evaluación iniciales.
        @details Registra los períodos 2019-2024 y 2025-2030 con sus
        fechas de inicio y fin correspondientes.
        """
        from datetime import date

        from evaluation.models import Periodo

        periodos = [
            {
                "nombre": "Periodo 2019-2024",
                "fecha_inicio": date(2019, 1, 1),
                "fecha_fin": date(2024, 12, 31),
                "activo": False,
            },
            {
                "nombre": "Periodo 2025-2030",
                "fecha_inicio": date(2025, 1, 1),
                "fecha_fin": date(2030, 12, 31),
                "activo": True,
            },
        ]

        for periodo in periodos:
            Periodo.objects.get_or_create(
                nombre=periodo["nombre"],
                defaults={
                    "fecha_inicio": periodo["fecha_inicio"],
                    "fecha_fin": periodo["fecha_fin"],
                    "activo": periodo["activo"],
                },
            )

        self.stdout.write(self.style.SUCCESS("Períodos registrados correctamente."))

    def seed_criterios(self):
        """@brief Crea los criterios de evaluación iniciales.
        @details Registra los 8 criterios de evaluación institucional
        asociados al período 2025-2030.
        """
        from evaluation.models import Criterio, Periodo

        periodo = Periodo.objects.get(nombre="Periodo 2025-2030")

        criterios = [
            {
                "nombre": "Gestión Institucional",
                "descripcion": "Evalúa la planificación estratégica, el gobierno institucional y los procesos de gestión administrativa.",
            },
            {
                "nombre": "Gestión Académica",
                "descripcion": "Evalúa la calidad de los procesos de enseñanza, el desarrollo curricular y la gestión de la oferta académica.",
            },
            {
                "nombre": "Investigación",
                "descripcion": "Evalúa las actividades de investigación, innovación, producción científica y desarrollo del conocimiento.",
            },
            {
                "nombre": "Vinculación con el Medio",
                "descripcion": "Evalúa la relación de la institución con la sociedad mediante extensión, cooperación y responsabilidad social.",
            },
            {
                "nombre": "Estudiantes",
                "descripcion": "Evalúa los procesos de admisión, permanencia, bienestar, desarrollo y seguimiento de los estudiantes.",
            },
            {
                "nombre": "Personal Académico",
                "descripcion": "Evalúa la gestión, desarrollo, formación y desempeño del personal docente.",
            },
            {
                "nombre": "Servicios y Estructuras de Apoyo",
                "descripcion": "Evalúa la infraestructura, recursos tecnológicos, bibliotecas y demás servicios de apoyo institucional.",
            },
            {
                "nombre": "Aseguramiento de la Calidad",
                "descripcion": "Evalúa los mecanismos institucionales para la mejora continua y el aseguramiento de la calidad.",
            },
        ]

        for criterio in criterios:
            Criterio.objects.get_or_create(
                nombre=criterio["nombre"],
                periodo=periodo,
                defaults={
                    "descripcion": criterio["descripcion"],
                    "activo": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Criterios registrados correctamente."))

    def seed_roles(self):
        """@brief Crea los roles iniciales del sistema.
        @details Registra los 6 grupos de usuarios: Administrador General,
        Consulta, Responsable Departamental, Revisor Institucional,
        Coordinador Quinquenal y Evaluador Externo.
        """
        from django.contrib.auth.models import Group

        roles = [
            "Administrador General",
            "Consulta",
            "Responsable Departamental",
            "Revisor Institucional",
            "Coordinador Quinquenal",
            "Evaluador Externo",
        ]

        for role_name in roles:
            Group.objects.get_or_create(name=role_name)

        self.stdout.write(self.style.SUCCESS("Roles iniciales registrados correctamente."))

    def seed_groups(self):
        """@brief Asigna permisos a los grupos de usuarios.
        @details Sincroniza los permisos definidos en ROLE_PERMISSIONS con
        cada grupo registrado en el sistema.
        """
        from django.contrib.auth.models import Group

        from accounts.role_permissions import ROLE_PERMISSIONS, sync_group_permissions

        for role_name in ROLE_PERMISSIONS:
            group, _ = Group.objects.get_or_create(name=role_name)
            sync_group_permissions(group)

        self.stdout.write(self.style.SUCCESS("Permisos iniciales asignados correctamente."))
