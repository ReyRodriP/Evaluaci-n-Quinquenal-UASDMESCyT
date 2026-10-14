"""Comando de validación e importación del catálogo EQ-SIDACES.

Solo validación en esta fase: la importación real a PostgreSQL queda para una etapa posterior
con aprobación explícita. --apply existe para las pruebas (SQLite/BD de prueba) y para la futura
importación controlada.

Modos (exactamente uno):
  --check      valida el archivo y reporta; no toca la BD.
  --dry-run    simula la importación en una transacción y la revierte; no persiste nada.
  --apply      importa (requerido --allow-synthetic-codes cuando hay indicadores sin codigo).

El flag se llama --marco-version porque --version esta reservado por Django (base.py).

Reglas de negocio:
  * Solo se importan registros estado=confirmado cuyos ancestros sean confirmados.
  * Las discrepancias entre meta.conteos_referencia y los conteos reales bloquean
    --dry-run/--apply salvo --ack-discrepancias (en --check solo se reportan).
  * Indicadores/evidencias sin codigo oficial: con --allow-synthetic-codes se genera un codigo
    sintetico no oficial (ej. 2.2.1.3-IND-01); sin el flag, --apply falla.
  * Evidencias: el modelo exige un IndicadorMarco; por eso solo se importan las que esten
    asociadas a un indicador (padre 'ind:...'); las del dataset (asociadas al estandar) quedan
    pendientes y no se importan.
"""

import csv
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalogo.models import (
    Componente,
    CriterioMarco,
    Dimension,
    Estandar,
    EvidenciaIndicativa,
    IndicadorMarco,
    VersionMarcoEvaluacion,
)

NIVELES = ["dimension", "componente", "criterio", "estandar", "indicador", "evidencia"]
PADRE_NIVEL = {
    "dimension": None,
    "componente": "dimension",
    "criterio": "componente",
    "estandar": "criterio",
    "indicador": "estandar",
    "evidencia": "indicador",
}
ROMANOS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}


class Command(BaseCommand):
    help = (
        "Importa y valida catalogo EQ-SIDACES (solo validacion en esta fase; "
        "--apply reservado para pruebas/importacion controlada)"
    )

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, required=True, help="Archivo normalizado (JSON o CSV)")
        parser.add_argument(
            "--marco-version",
            dest="marco_version",
            type=str,
            required=True,
            help="Version del marco; debe coincidir con el campo version_marco del archivo "
            "(se llama asi porque --version esta reservado por Django)",
        )
        parser.add_argument("--check", action="store_true", help="Solo validar el archivo, sin tocar la BD")
        parser.add_argument("--dry-run", action="store_true", help="Simular la importacion y revertirla")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Importar de verdad (en esta fase: solo BD de pruebas)",
        )
        parser.add_argument(
            "--ack-discrepancias",
            action="store_true",
            dest="ack_discrepancias",
            help="Reconoce explicitamente las discrepancias de conteo frente a la referencia oficial",
        )
        parser.add_argument(
            "--allow-synthetic-codes",
            action="store_true",
            dest="allow_synthetic_codes",
            help="Permite generar codigos sinteticos (no oficiales) para indicadores sin codigo",
        )

    # ------------------------------------------------------------------
    # carga
    # ------------------------------------------------------------------

    def _cargar(self, path):
        try:
            with open(path, encoding="utf-8") as fh:
                if path.endswith(".json"):
                    datos = json.load(fh)
                else:
                    datos = list(csv.DictReader(fh))
        except Exception as exc:  # noqa: BLE001
            raise CommandError(f"Error leyendo archivo: {exc}")

        meta = None
        if isinstance(datos, dict):
            meta = datos.get("meta")
            registros = datos.get("registros")
            if not isinstance(registros, list):
                raise CommandError("El JSON no contiene la lista 'registros'")
        elif isinstance(datos, list):
            registros = datos
        else:
            raise CommandError("Formato no soportado: se esperaba JSON ({meta, registros}) o CSV")
        return registros, meta

    # ------------------------------------------------------------------
    # validacion de archivo
    # ------------------------------------------------------------------

    def _validar(self, registros, meta, marco_version):
        errores = []
        avisos = []
        if not registros:
            return ["El archivo no contiene registros"], avisos

        claves = set()
        por_clave = {}
        for i, reg in enumerate(registros, start=1):
            pref = f"Fila {i}"
            if not isinstance(reg, dict):
                errores.append(f"{pref}: no es un objeto")
                continue
            for campo in ("clave", "nivel", "texto_original", "estado", "orden"):
                if campo not in reg:
                    errores.append(f"{pref}: falta el campo '{campo}'")
            clave = reg.get("clave")
            if not clave:
                errores.append(f"{pref}: clave vacia")
            else:
                if clave in claves:
                    errores.append(f"{pref}: clave duplicada '{clave}'")
                claves.add(clave)
                por_clave[clave] = reg
            nivel = reg.get("nivel")
            if nivel and nivel not in NIVELES:
                errores.append(f"{pref}: nivel desconocido '{nivel}'")
            estado = reg.get("estado")
            if estado and estado not in ("confirmado", "pendiente_revision"):
                errores.append(f"{pref}: estado desconocido '{estado}'")
            try:
                orden = int(reg.get("orden", 0))
                if orden < 1:
                    raise ValueError
            except (TypeError, ValueError):
                errores.append(f"{pref}: orden invalido '{reg.get('orden')}'")
            version = reg.get("version_marco")
            if version and version != marco_version:
                errores.append(
                    f"{pref}: version_marco '{version}' no coincide con --marco-version "
                    f"'{marco_version}'"
                )
            nj = reg.get("nivel_jerarquico")
            if (
                nivel in NIVELES
                and str(nj).isdigit()
                and int(nj) != NIVELES.index(nivel) + 1
            ):
                errores.append(f"{pref}: nivel_jerarquico {nj} no corresponde a '{nivel}'")

        # jerarquia y reglas por registro
        for i, reg in enumerate(registros, start=1):
            if not isinstance(reg, dict):
                continue
            pref = f"Fila {i} ({reg.get('clave')})"
            nivel = reg.get("nivel")
            if nivel not in NIVELES:
                continue
            padre = reg.get("padre") or None
            esperado = PADRE_NIVEL[nivel]
            confirmado_check = reg.get("estado") == "confirmado"
            if esperado is None:
                if padre:
                    errores.append(f"{pref}: {nivel} no debe tener padre")
            else:
                p = por_clave.get(padre)
                if p is None:
                    errores.append(f"{pref}: padre '{padre}' inexistente")
                elif confirmado_check and p.get("nivel") != esperado:
                    # en registros pendientes se conserva la asociacion de la fuente
                    # (p. ej. evidencias pendientes asociadas a su estandar)
                    errores.append(
                        f"{pref}: el padre '{padre}' es {p.get('nivel')}, se esperaba {esperado}"
                    )
            confirmado = reg.get("estado") == "confirmado"
            texto = (reg.get("texto_original") or "").strip()
            if confirmado and not texto:
                errores.append(f"{pref}: confirmado sin texto")
            codigo = (reg.get("codigo") or "").strip()
            if confirmado and nivel in ("componente", "criterio", "estandar") and not codigo:
                errores.append(f"{pref}: {nivel} confirmado sin codigo")
            if confirmado and nivel == "indicador" and codigo:
                avisos.append(f"{pref}: indicador con codigo propio '{codigo}'")
            if confirmado and nivel == "evidencia":
                if not padre or not str(padre).startswith("ind:"):
                    errores.append(
                        f"{pref}: evidencia confirmada debe tener padre indicador "
                        "(la matriz no determina la asociacion)"
                    )
            # coherencia de prefijos para confirmados
            if confirmado and codigo and padre:
                p = por_clave.get(padre)
                if p is not None:
                    pcodigo = (p.get("codigo") or "").strip()
                    if nivel == "componente" and pcodigo:
                        esperado_n = ROMANOS.get(pcodigo)
                        if esperado_n and not codigo.startswith(f"{esperado_n}."):
                            errores.append(
                                f"{pref}: codigo '{codigo}' no corresponde a la dimension {pcodigo}"
                            )
                    elif nivel in ("criterio", "estandar") and pcodigo:
                        if not codigo.startswith(pcodigo + "."):
                            errores.append(
                                f"{pref}: codigo '{codigo}' no corresponde al padre '{pcodigo}'"
                            )

        # unicidad de codigos confirmados a nivel global (unique_together de la BD)
        vistos = {}
        for reg in registros:
            if not isinstance(reg, dict) or reg.get("estado") != "confirmado":
                continue
            codigo = (reg.get("codigo") or "").strip()
            nivel = reg.get("nivel")
            if not codigo or nivel not in ("componente", "criterio", "estandar"):
                continue
            if codigo in vistos:
                errores.append(
                    f"codigo '{codigo}' repetido entre confirmados ({vistos[codigo]} y {reg.get('clave')})"
                )
            else:
                vistos[codigo] = reg.get("clave")

        # contraste de conteos contra la referencia oficial
        discrepancias = []
        referencias = {}
        if not meta or "conteos_referencia" not in (meta or {}):
            avisos.append(
                "El archivo no trae meta.conteos_referencia: no se pueden contrastar conteos "
                "(se recomienda el JSON generado por scripts/extraer_eq_sidaces.py)"
            )
        else:
            referencias = meta["conteos_referencia"]
            reales = {}
            for nivel in NIVELES:
                reales[nivel] = sum(1 for r in registros if isinstance(r, dict) and r.get("nivel") == nivel)
            for nivel in NIVELES:
                ref = referencias.get(nivel)
                real = reales.get(nivel, 0)
                if ref is not None and real != ref:
                    discrepancias.append((nivel, real, ref, real - ref))
        # definiciones solo disponibles en JSON
        if any(
            isinstance(r, dict)
            and r.get("nivel") == "componente"
            and "origen" not in r
            for r in registros
        ):
            avisos.append(
                "Registros de componente sin 'origen.definicion' (¿CSV?): las definiciones "
                "solo estan en el JSON; se importaran vacias"
            )

        return errores, avisos, discrepancias

    # ------------------------------------------------------------------
    # reporte
    # ------------------------------------------------------------------

    @staticmethod
    def _conteos(registros):
        resumen = {}
        for nivel in NIVELES:
            del_nivel = [r for r in registros if isinstance(r, dict) and r.get("nivel") == nivel]
            resumen[nivel] = {
                "total": len(del_nivel),
                "confirmados": sum(1 for r in del_nivel if r.get("estado") == "confirmado"),
                "pendientes": sum(1 for r in del_nivel if r.get("estado") == "pendiente_revision"),
            }
        return resumen

    def _reportar(self, registros, meta, discrepancias, avisos):
        resumen = self._conteos(registros)
        self.stdout.write(f"Registros leidos: {len(registros)}")
        for nivel in NIVELES:
            d = resumen[nivel]
            self.stdout.write(
                f"  {nivel:11s} total={d['total']:4d} confirmados={d['confirmados']:4d} "
                f"pendientes={d['pendientes']:4d}"
            )
        pendientes = [
            r
            for r in registros
            if isinstance(r, dict) and r.get("estado") == "pendiente_revision" and r.get("nivel") != "evidencia"
        ]
        if pendientes:
            self.stdout.write(f"Pendientes de revision (excluye evidencias): {len(pendientes)}")
            for r in pendientes[:10]:
                obs_raw = r.get("observaciones") or []
                obs = (obs_raw if isinstance(obs_raw, str) else "; ".join(obs_raw))
                obs = obs[:100] or "sin observacion"
                self.stdout.write(f"  - {r.get('clave')}: {obs}")
        evidencias = resumen["evidencia"]["pendientes"]
        if evidencias:
            self.stdout.write(
                f"  ... y {evidencias} evidencias pendientes (asociacion evidencia->indicador "
                "no determinable en la matriz)"
            )
        if discrepancias:
            self.stdout.write(self.style.WARNING("Discrepancias de conteo frente a meta.conteos_referencia:"))
            for nivel, real, ref, delta in discrepancias:
                signo = "+" if delta > 0 else ""
                self.stdout.write(
                    f"  {nivel:11s} extraidos={real:4d} referencia={ref:4d} ({signo}{delta}) "
                    "=> requiere revision manual o --ack-discrepancias"
                )
        for aviso in avisos:
            self.stdout.write(self.style.WARNING(f"Aviso: {aviso}"))
        if meta:
            incidencias = meta.get("incidencias") or []
            if incidencias:
                self.stdout.write(f"Incidencias registradas en meta: {len(incidencias)}")

    # ------------------------------------------------------------------
    # importacion
    # ------------------------------------------------------------------

    def _importar(self, registros, marco_version, allow_synthetic, dry_run):
        slug = slugify(marco_version)
        stats = {
            "nuevos": {n: 0 for n in NIVELES},
            "existentes": {n: 0 for n in NIVELES},
            "omitidos": {"pendiente": 0, "padre_omitido": 0},
            "sinteticos": 0,
        }

        with transaction.atomic():
            version, creada = VersionMarcoEvaluacion.objects.get_or_create(
                slug=slug,
                defaults={
                    "nombre": marco_version,
                    "fuente": "docs/Estándares Marco EQ-SIDACES (Versión Final).pdf",
                    "nota": "Importada por import_eq_sidaces; estado 'activo' no se modifica en esta fase.",
                },
            )
            self.stdout.write(
                f"VersionMarcoEvaluacion '{version.nombre}' (slug={slug}): "
                + ("creada" if creada else "existente")
            )
            if not version.activo:
                self.stdout.write(
                    self.style.WARNING(
                        "La version no esta activa; el flag activo no se modifica en esta fase "
                        "(solo puede haber una version activa)."
                    )
                )

            mapeo = {}
            for reg in registros:
                if not isinstance(reg, dict):
                    continue
                if reg.get("estado") != "confirmado":
                    stats["omitidos"]["pendiente"] += 1
                    continue
                clave = reg.get("clave")
                padre = reg.get("padre") or None
                if padre and padre not in mapeo:
                    stats["omitidos"]["padre_omitido"] += 1
                    continue
                nivel = reg.get("nivel")
                texto = (reg.get("texto_original") or "").strip()
                codigo = (reg.get("codigo") or "").strip()
                orden = int(reg.get("orden"))

                if nivel == "dimension":
                    obj, nueva = Dimension.objects.get_or_create(
                        version_marco=version,
                        codigo=codigo,
                        defaults={"nombre": texto, "orden": orden},
                    )
                elif nivel == "componente":
                    definicion = (reg.get("origen") or {}).get("definicion", "")
                    obj, nueva = Componente.objects.get_or_create(
                        version_marco=version,
                        codigo_completo=codigo,
                        defaults={
                            "dimension": mapeo[padre],
                            "codigo": codigo,
                            "nombre": texto,
                            "definicion": definicion,
                            "orden": orden,
                        },
                    )
                elif nivel == "criterio":
                    obj, nueva = CriterioMarco.objects.get_or_create(
                        version_marco=version,
                        codigo_completo=codigo,
                        defaults={
                            "componente": mapeo[padre],
                            "codigo": codigo,
                            "nombre": texto,
                            "orden": orden,
                        },
                    )
                elif nivel == "estandar":
                    obj, nueva = Estandar.objects.get_or_create(
                        version_marco=version,
                        codigo_completo=codigo,
                        defaults={
                            "criterio_marco": mapeo[padre],
                            "codigo": codigo,
                            "redaccion": texto,
                            "orden": orden,
                        },
                    )
                elif nivel == "indicador":
                    if not codigo:
                        if not allow_synthetic and not dry_run:
                            raise CommandError(
                                "Indicadores sin codigo oficial: reejecute con "
                                "--allow-synthetic-codes para generar codigos sinteticos"
                            )
                        codigo = f"{padre.replace('std:', '')}-IND-{orden:02d}"
                        stats["sinteticos"] += 1
                    obj, nueva = IndicadorMarco.objects.get_or_create(
                        version_marco=version,
                        codigo_completo=codigo,
                        defaults={
                            "estandar": mapeo[padre],
                            "codigo": codigo,
                            "redaccion_oficial": texto,
                            "orden": orden,
                            "activo": True,
                        },
                    )
                elif nivel == "evidencia":
                    if not padre or not str(padre).startswith("ind:"):
                        stats["omitidos"]["padre_omitido"] += 1
                        continue
                    if not codigo:
                        if not allow_synthetic and not dry_run:
                            raise CommandError(
                                "Evidencias sin codigo oficial: reejecute con "
                                "--allow-synthetic-codes para generar codigos sinteticos"
                            )
                        codigo = f"{padre.replace('ind:', '')}-EV-{orden:02d}"
                        stats["sinteticos"] += 1
                    obj, nueva = EvidenciaIndicativa.objects.get_or_create(
                        version_marco=version,
                        codigo_completo=codigo,
                        defaults={
                            "indicador_marco": mapeo[padre],
                            "codigo": codigo,
                            "descripcion": texto,
                            "orden": orden,
                            "obligatoria": None,
                        },
                    )
                else:
                    continue
                mapeo[clave] = obj
                stats["nuevos" if nueva else "existentes"][nivel] += 1

            if dry_run:
                transaction.set_rollback(True)
        return stats

    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        modos = [options["check"], options["dry_run"], options["apply"]]
        if sum(1 for m in modos if m) != 1:
            raise CommandError(
                "Debe especificar exactamente un modo: --check, --dry-run o --apply "
            )

        registros, meta = self._cargar(options["file"])
        errores, avisos, discrepancias = self._validar(registros, meta, options["marco_version"])

        self.stdout.write(self.style.SUCCESS(f"Archivo: {options['file']}"))
        self.stdout.write(f"Version: {options['marco_version']}")
        self.stdout.write(f"Modo: {'check' if options['check'] else 'dry-run' if options['dry_run'] else 'apply'}")
        self._reportar(registros, meta, discrepancias, avisos)

        if errores:
            for e in errores[:20]:
                self.stdout.write(self.style.ERROR(e))
            if len(errores) > 20:
                self.stdout.write(self.style.ERROR(f"... y {len(errores) - 20} errores mas"))
            raise CommandError(f"Validacion fallida: {len(errores)} error(es)")

        if options["check"]:
            self.stdout.write(self.style.SUCCESS("Validacion de archivo completada sin errores criticos"))
            return

        if discrepancias and not options["ack_discrepancias"]:
            raise CommandError(
                "Discrepancias de conteo frente a la referencia oficial: revise "
                "docs/auditoria_eq_sidaces.md y reejecute con --ack-discrepancias para continuar"
            )

        stats = self._importar(
            registros,
            options["marco_version"],
            options["allow_synthetic_codes"],
            options["dry_run"],
        )

        for nivel in NIVELES:
            self.stdout.write(
                f"  {nivel:11s} nuevos={stats['nuevos'][nivel]:4d} "
                f"existentes={stats['existentes'][nivel]:4d}"
            )
        self.stdout.write(
            f"Omitidos: pendiente_revision={stats['omitidos']['pendiente']}, "
            f"padre omitido={stats['omitidos']['padre_omitido']}"
        )
        if stats["sinteticos"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Codigos sinteticos generados (no oficiales): {stats['sinteticos']}"
                )
            )
            if options["dry_run"] and not options["allow_synthetic_codes"]:
                self.stdout.write(
                    self.style.WARNING(
                        "Para aplicar esta importacion se requiere --allow-synthetic-codes"
                    )
                )
        if options["dry_run"]:
            self.stdout.write(
                self.style.SUCCESS("dry-run completado: la transaccion fue revertida, nada persistio")
            )
        else:
            self.stdout.write(self.style.SUCCESS("Importacion aplicada"))
