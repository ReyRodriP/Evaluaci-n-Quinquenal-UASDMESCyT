from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Carga los datos iniciales del sistema"

    def handle(self, *args, **kwargs):
        self.seed_facultades()
        self.seed_departamentos()
        self.seed_roles()
        self.seed_permisos()

        self.stdout.write(
            self.style.SUCCESS("Datos iniciales cargados correctamente.")
        )

    def seed_facultades(self):
        from organization.models import Facultad

        facultades = [
            {
                "nombre": "Facultad de Humanidades",
                "descripcion": "Responsable de la formación académica e investigación en las áreas de humanidades, letras, filosofía, historia y disciplinas afines."
            },
            {
                "nombre": "Facultad de Ciencias",
                "descripcion": "Desarrolla programas académicos e investigaciones en ciencias básicas como matemática, física, química, biología e informática."
            },
            {
                "nombre": "Facultad de Ciencias Económicas y Sociales",
                "descripcion": "Forma profesionales en economía, administración, contabilidad, mercadeo, sociología y otras ciencias sociales."
            },
            {
                "nombre": "Facultad de Ciencias Jurídicas y Políticas",
                "descripcion": "Promueve la formación de profesionales en derecho, ciencias políticas y áreas relacionadas con la administración de justicia."
            },
            {
                "nombre": "Facultad de Ingeniería y Arquitectura",
                "descripcion": "Desarrolla la formación de ingenieros y arquitectos mediante programas académicos orientados a la innovación y el desarrollo tecnológico."
            },
            {
                "nombre": "Facultad de Ciencias de la Salud",
                "descripcion": "Forma profesionales de la salud y fomenta la investigación en medicina, odontología, enfermería y disciplinas afines."
            },
            {
                "nombre": "Facultad de Ciencias Agronómicas y Veterinarias",
                "descripcion": "Impulsa la formación e investigación en agricultura, producción animal, veterinaria y desarrollo sostenible."
            },
            {
                "nombre": "Facultad de Artes",
                "descripcion": "Promueve la formación artística y cultural en áreas como música, teatro, danza, artes visuales y diseño."
            },
            {
                "nombre": "Facultad de Ciencias de la Educación",
                "descripcion": "Forma profesionales de la educación y desarrolla investigaciones orientadas al mejoramiento de los procesos de enseñanza y aprendizaje."
            },
        ]

        for facultad in facultades:
            Facultad.objects.get_or_create(
                nombre=facultad["nombre"],
                defaults={
                    "descripcion": facultad["descripcion"]
                }
            )

        self.stdout.write(self.style.SUCCESS("Facultades registradas correctamente."))

    def seed_departamentos(self):
        from organization.models import Facultad, Departamento

        facultad_ciencias = Facultad.objects.get(
            nombre="Facultad de Ciencias"
        )

        departamentos = [
            {
                "nombre": "Escuela de Biología",
                "descripcion": "Unidad académica dedicada a la formación e investigación en las ciencias biológicas."
            },
            {
                "nombre": "Escuela de Física",
                "descripcion": "Unidad académica responsable de la enseñanza e investigación en física y sus aplicaciones."
            },
            {
                "nombre": "Escuela de Geografía",
                "descripcion": "Unidad académica orientada al estudio del espacio geográfico, el medio ambiente y el ordenamiento territorial."
            },
            {
                "nombre": "Escuela de Informática",
                "descripcion": "Unidad académica dedicada a la formación de profesionales en informática, desarrollo de software y tecnologías de la información."
            },
            {
                "nombre": "Escuela de Matemáticas",
                "descripcion": "Unidad académica encargada de la formación e investigación en matemáticas puras y aplicadas."
            },
            {
                "nombre": "Escuela de Microbiología y Parasitología",
                "descripcion": "Unidad académica especializada en el estudio de microorganismos, parásitos y su impacto en la salud y el medio ambiente."
            },
            {
                "nombre": "Escuela de Química",
                "descripcion": "Unidad académica dedicada a la enseñanza e investigación en química y ciencias afines."
            },
        ]

        for departamento in departamentos:
            Departamento.objects.get_or_create(
                nombre=departamento["nombre"],
                facultad=facultad_ciencias,
                defaults={
                    "descripcion": departamento["descripcion"]
                }
            )

        self.stdout.write(
            self.style.SUCCESS("Departamentos de la Facultad de Ciencias registrados correctamente.")
        )

    def seed_roles(self):
        from django.contrib.auth.models import Group

        roles = [
            'Administrador General',
            'Consulta',
            'Responsable Departamental',
            'Revisor Institucional',
            'Coordinador Quinquenal',
            'Evaluador Externo'
        ]

        for role_name in roles:
            Group.objects.get_or_create(name=role_name)

        self.stdout.write(self.style.SUCCESS('Roles iniciales registrados correctamente.'))

    def seed_permisos(self):
        self.stdout.write(self.style.WARNING('Semilla de permisos no implementada.'))