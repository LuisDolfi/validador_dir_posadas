from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
import json

class Command(BaseCommand):
    help = "Formatea (pretty) un GeoJSON y lo guarda en data/pretty/"

    def add_arguments(self, parser):
        parser.add_argument("input", type=str, help="Ruta al GeoJSON RAW")
        parser.add_argument("-o", "--output", type=str, default=None,
                            help="Ruta de salida (opcional). Por defecto: data/pretty/<nombre>_pretty.json")
        parser.add_argument("--indent", type=int, default=2, help="Espacios de indentación (default 2)")
        parser.add_argument("--sort-keys", action="store_true", help="Ordenar claves al serializar")
        parser.add_argument("--drop-null-props", action="store_true",
                            help="Quita propiedades con valor null en cada feature")

    def handle(self, *args, **opts):
        in_path = Path(opts["input"])
        if not in_path.is_absolute():
            in_path = (settings.ROOT_DIR / in_path).resolve()
        if not in_path.exists():
            raise CommandError(f"No existe el archivo: {in_path}")

        # Cargar JSON
        try:
            with open(in_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise CommandError(f"No se pudo leer JSON: {e}")

        # Opcional: limpiar props null
        if opts.get("drop_null_props"):
            feats = data.get("features", [])
            for feat in feats:
                props = feat.get("properties")
                if isinstance(props, dict):
                    feat["properties"] = {k: v for k, v in props.items() if v is not None}

        # Salida por defecto
        out_path = opts.get("output")
        if out_path:
            out_path = Path(out_path)
            if not out_path.is_absolute():
                out_path = (settings.ROOT_DIR / out_path).resolve()
        else:
            out_dir = (settings.ROOT_DIR / "data" / "pretty")
            out_dir.mkdir(parents=True, exist_ok=True)
            base = in_path.stem + "_pretty.json"
            out_path = out_dir / base

        # Escribir pretty
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=opts.get("indent", 2),
                sort_keys=opts.get("sort_keys", False),
            )

        self.stdout.write(self.style.SUCCESS(f"Escrito: {out_path}"))
