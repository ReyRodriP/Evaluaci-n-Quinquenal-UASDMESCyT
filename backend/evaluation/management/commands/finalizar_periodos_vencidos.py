from django.core.management.base import BaseCommand

from evaluation.services import finalizar_periodos_vencidos


class Command(BaseCommand):
    help = "Desactiva los períodos cuya fecha de finalización ya pasó."

    def handle(self, *args, **options):
        cantidad = finalizar_periodos_vencidos()
        self.stdout.write(self.style.SUCCESS(f"Períodos desactivados: {cantidad}"))
