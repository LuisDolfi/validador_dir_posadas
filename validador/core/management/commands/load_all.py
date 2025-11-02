# validador/core/management/commands/load_all.py
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command, CommandError

# patrones -> (etiqueta, tipo)
MAP = {
    "cuadricula_posadas_*_pretty.json": ("cuadricula", "json"),  # 👈 forzamos json
    "avenidas_posadas_*_pretty.json": ("avenida", "avenida"),
    "chacras_posadas_*_pretty.json": ("chacra", "chacra"),
    "manzanero_posadas_*_pretty.json": ("manzanero", "manzanero"),
    "cuadricula_posadas_*_pretty.json": ("cuadricula", "cuadricula"),
    "edificios_posadas_*_pretty.json": ("edificio", "edificio"),
}

class Command(BaseCommand):
    help = "Carga todas las capas data/pretty/*.json en PostGIS usando load_geojson"

    def add_arguments(self, parser):
        parser.add_argument("--overwrite", action="store_true", help="Recrear registros si existen")
        parser.add_argument("--limit", type=int, default=0, help="Procesar hasta N archivos (0 = todos)")

    def handle(self, *args, **opts):
        root = Path(getattr(settings, "ROOT_DIR", settings.BASE_DIR))
        pretty = (root / "data" / "pretty").resolve()
        if not pretty.exists():
            raise CommandError(f"No existe {pretty}")

        done = failed = skipped = 0
        files = []

        # recopila archivos por patrón en orden alfabético
        for pattern, (_tag, _tipo) in MAP.items():
            found = sorted(pretty.glob(pattern))
            files.extend([(path, _tipo) for path in found])

        if opts["limit"] > 0:
            files = files[: opts["limit"]]

        for path, tipo in files:
            try:
                call_command("load_geojson", str(path), "--type", tipo, verbosity=0)
                self.stdout.write(self.style.SUCCESS(f"OK  {path.name}"))
                done += 1
            except Exception as e:
                failed += 1
                self.stderr.write(self.style.ERROR(f"FAIL {path.name}: {e!s}"))

        # resumen
        self.stdout.write(self.style.SUCCESS(f"Listo: {done} ✓ | Fail: {failed}"))
