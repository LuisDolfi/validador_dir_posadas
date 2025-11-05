"""
Comando especializado para cargar calles y avenidas de Posadas
a partir de los GeoJSON oficiales (IDE Posadas 2025).
Usa clean_name() para extraer el nombre limpio sin número ni prefijo.
"""


from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, MultiLineString
from validador.core.models import Street
import json, re

def load_geojson(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_name(raw: str) -> str:
    s = (raw or "").strip()
    # quita "CALLE " o "AVENIDA " al inicio (o abreviado) y el número final entre paréntesis
    s = re.sub(r"\(\s*\d+\s*\)\s*$", "", s, flags=re.I)             # ... (49)
    s = re.sub(r"^(AVENIDA|AV\.|CALLE|C\.)\s+", "", s, flags=re.I)  # prefijo
    return s.strip().title()  # "CALLE JUJUY" -> "Jujuy"

def to_mls(geom):
    """Convierte LineString->MultiLineString si hace falta."""
    if geom.geom_type == "LineString":
        return MultiLineString(geom)
    return geom

class Command(BaseCommand):
    help = "Carga avenidas y calles de Posadas en core_street"

    def add_arguments(self, parser):
        parser.add_argument("--avenidas", required=True, help="avenidas_posadas_2025-09-17_pretty.json")
        parser.add_argument("--calles",   required=True, help="calles_posadas_2025-09-17_pretty.json")

    def handle(self, *args, **opts):
        av = load_geojson(opts["avenidas"])
        ca = load_geojson(opts["calles"])

        n_av = n_ca = 0

        # Avenidas: campo 'avenidas' (string tipo "AVENIDA ROQUE PEREZ(26)")
        for feat in av.get("features", []):
            props = feat.get("properties", {})
            raw = props.get("avenidas") or props.get("AVENIDAS") or ""
            name = clean_name(raw)
            geom = GEOSGeometry(json.dumps(feat["geometry"]))
            if geom.geom_type not in ("LineString", "MultiLineString"):
                continue
            Street.objects.create(kind="avenida", name=name, aliases=[], geom=to_mls(geom))
            n_av += 1

        # Calles: campo 'CALLE' (string tipo "CALLE JUJUY(49)")
        for feat in ca.get("features", []):
            props = feat.get("properties", {})
            raw = props.get("CALLE") or props.get("calle") or ""
            name = clean_name(raw)
            geom = GEOSGeometry(json.dumps(feat["geometry"]))
            if geom.geom_type not in ("LineString", "MultiLineString"):
                continue
            Street.objects.create(kind="calle", name=name, aliases=[], geom=to_mls(geom))
            n_ca += 1

        self.stdout.write(self.style.SUCCESS(f"Cargadas {n_av} avenidas y {n_ca} calles"))
