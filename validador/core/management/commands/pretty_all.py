from django.core.management.base import BaseCommand
from django.core.management import call_command, CommandError
from django.conf import settings
from pathlib import Path

class Command(BaseCommand):
    help = "Convierte todos los data/raw/*.json a data/pretty/*_pretty.json usando pretty_geojson."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Sobrescribe archivos existentes en pretty/."
        )

    def handle(self, *args, **opts):
        root = Path(getattr(settings, "ROOT_DIR", settings.BASE_DIR)).resolve()
        raw_dir = (root / "data" / "raw").resolve()
        out_dir = (root / "data" / "pretty").resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        if not raw_dir.exists():
            raise CommandError(f"No existe {raw_dir}")

        files = sorted(raw_dir.glob("*.json"))
        if not files:
            self.stdout.write(self.style.WARNING("No hay JSON en data/raw"))
            return

        done, skipped, failed = 0, 0, 0
        for src in files:
            # nombre destino
            stem = src.stem
            if stem.endswith("_raw"):
                stem = stem[:-4]
            dst = out_dir / f"{stem}_pretty.json"

            if dst.exists() and not opts["overwrite"]:
                skipped += 1
                self.stdout.write(self.style.NOTICE(f"Skip (existe): {dst.name}"))
                continue

            try:
                call_command(
                    "pretty_geojson",
                    str(src),
                    "-o", str(dst),
                    "--drop-null-props",
                    "--sort-keys",
                    verbosity=0,
                )
                done += 1
                self.stdout.write(self.style.SUCCESS(f"OK  → {dst.name}"))
            except Exception as e:
                failed += 1
                self.stderr.write(self.style.ERROR(f"FAIL {src.name}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Listo: {done} 👍  | Skip: {skipped} | Fail: {failed}"))
