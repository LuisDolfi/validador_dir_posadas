from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.gis.gdal import DataSource, GDALException
from django.contrib.gis.geos import GEOSGeometry, MultiLineString, MultiPolygon, Point
from validador.core.models import Street, BlockGrid, Building, Parcel
from pathlib import Path
import json
from django.apps import apps
# Modelos
Parcel    = apps.get_model('core', 'Parcel')
Street    = apps.get_model('core', 'Street')
BlockGrid = apps.get_model('core', 'BlockGrid')
Building  = apps.get_model('core', 'Building')

def pick_value(props: dict, preferred: list[str], fuzzy_terms: list[str] = None):
    """Devuelve props[k] para el primer k hallado. Si no aparece exacto,
    intenta fuzzy: cualquier clave que contenga alguno de los términos."""
    if not props:
        return None
    # 1) exactos (con distintas capitalizaciones)
    for key in preferred:
        for kk in (key, key.lower(), key.upper(), key.title()):
            if kk in props and props[kk] not in (None, ""):
                return props[kk]
    # 2) fuzzy por contains
    if fuzzy_terms:
        for k in props.keys():
            lk = k.lower()
            if any(term in lk for term in fuzzy_terms):
                val = props[k]
                if val not in (None, ""):
                    return val
    return None

def props_dict_gdal(feature):
    """Convierte feature GDAL a dict de propiedades."""
    try:
        d = dict(feature.fields)
    except Exception:
        d = {}
    return d

def get_prop(props, *candidates, default=None):
    for k in candidates:
        for kk in (k, k.lower(), k.upper(), k.title()):
            if isinstance(props, dict) and kk in props and props[kk] not in (None, ""):
                return props[kk]
    return default

def to_multi(geom: GEOSGeometry, expected: str) -> GEOSGeometry:
    # expected in {"MultiLineString","MultiPolygon"}
    if geom is None:
        return None
    if expected == "MultiLineString":
        if geom.geom_type == "LineString":
            return MultiLineString(geom)
    if expected == "MultiPolygon":
        if geom.geom_type == "Polygon":
            return MultiPolygon(geom)
    return geom  # para Point u otros

def read_features(path: Path):
    """Devuelve (features_iterable, mode) donde mode ∈ {'gdal','json'}"""
    try:
        ds = DataSource(str(path))
        return ds[0], 'gdal'
    except GDALException:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "features" not in data:
            raise CommandError("El JSON no contiene 'features'. Usá los archivos 'pretty' o conviértelo a GeoJSON válido.")
        return data["features"], 'json'

class Command(BaseCommand):
    help = "Carga archivos GeoJSON/JSON (calles, avenidas, chacras, edificios)"
    def props_of(feat):
        # Caso GeoJSON (feat es un dict con 'properties')
        if isinstance(feat, dict):
            return feat.get("properties", {}) or {}

        # Caso GDAL (feat es un OGRFeature)
        names = getattr(feat, "fields", None)
        if names:
            try:
                # names suele ser lista de nombres; get(name) da el valor
                return {name: feat.get(name) for name in names}
            except Exception:
                pass

        # Fallback: si por algún motivo vino lista/tupla, la convertimos a dict índice->valor
        if isinstance(feat, (list, tuple)):
            return {str(i): v for i, v in enumerate(feat)}

        return {}
    
    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Ruta al archivo (relativa o absoluta)")
        parser.add_argument("--type", choices=["calle", "avenida", "chacra", "edificio", "manzanero", "cuadricula"], help="Tipo de datos a importar")


    def handle(self, *args, **opts):
        raw = opts["path"]
        tipo = opts["type"]

        p = Path(raw)
        #p = Path(options['path'])
        if not p.is_absolute():
            p = (Path(settings.ROOT_DIR) / p).resolve()

# (opcional) mostrar la ruta final para confirmar
        self.stdout.write(self.style.NOTICE(f"Ruta resuelta: {p}"))

        if not p.exists():
            raise CommandError(f"No existe el archivo: {p}")

        layer, mode = read_features(p)
        self.stdout.write(self.style.NOTICE(f"Leyendo {p.name} vía {mode.upper()}"))

        inserted = 0
        total = len(layer)

        if mode == 'gdal':
            feats = layer
            def props_of(f): return f.fields
            def geom_of(f):
                g = f.geom.geos
                if g.srid is None:
                    g.srid = 4326
                return g
        else:
            feats = layer
            def props_of(f): return f.get("properties", {})
            def geom_of(f):
                g = GEOSGeometry(json.dumps(f.get("geometry")), srid=4326)
                if g.srid is None: g.srid = 4326
                return g

        if tipo == "calle":
            for f in feats:
                if mode == "gdal":
                    props = props_dict_gdal(f)
                else:
                    props = props_of(f)

                name = pick_value(
                    props,
                    preferred=["CALLE", "NOM_CALLE", "Nombre", "name", "NOMBRE"],
                    fuzzy_terms=["calle", "nom_calle", "nombre"]
                ) or "sin_nombre"

                if name == "sin_nombre":
                    self.stdout.write(self.style.WARNING(f"[{tipo}] Feature sin nombre. Claves disponibles: {list(props.keys())[:15]}..."))

                g = geom_of(f)
                Street.objects.create(
                    name=name.strip() if isinstance(name, str) else name,
                    kind="calle",
                    geom=to_multi(g, "MultiLineString"),
                )

        elif tipo == "avenida":
            for f in feats:
                if mode == "gdal":
                    props = props_dict_gdal(f)
                else:
                    props = props_of(f)

                name = pick_value(
                    props,
                    preferred=["AVENIDA", "AVENIDAS", "Nombre", "name", "NOMBRE"],
                    fuzzy_terms=["avenid", "nombre"]
                ) or "sin_nombre"

                if name == "sin_nombre":
                    self.stdout.write(self.style.WARNING(f"[{tipo}] Feature sin nombre. Claves disponibles: {list(props.keys())[:15]}..."))

                g = geom_of(f)
                Street.objects.create(
                    name=name.strip() if isinstance(name, str) else name,
                    kind="avenida",
                    geom=to_multi(g, "MultiLineString"),
                )

        elif tipo == "edificio":
            for f in feats:
                props = props_dict_gdal(f) if mode == "gdal" else props_of(f)

                barrio   = pick_value(props, ["BARRIO","barrio"], ["barr"])
                chacra   = pick_value(props, ["CHACRA","chacra","CH","Ch"], ["chac"])
                manzana  = pick_value(props, ["MANZANA","manzana","MZ","Mzna","Manz"], ["manz","mz"])
                numero   = pick_value(props, ["NUMERO","numero","NRO","nro","NUM","num"], ["num"])
                letra    = pick_value(props, ["LETRA","letra","Letra"], ["letr"])
                escalera = pick_value(props, ["ESCALERA","escalera","Esc","ESC"], ["escal"])

                g = geom_of(f)  # puede ser Point, Polygon, MultiPolygon, MultiPoint…

                # Normalizamos a Point:
                if g.geom_type == "Point":
                    pass
                elif g.geom_type in ("Polygon", "MultiPolygon"):
                    g = g.centroid  # tomamos centroide de la planta
                elif g.geom_type == "MultiPoint":
                    g = list(g)[0]  # primer punto
                else:
                    # último recurso: centroide de lo que sea
                    g = g.centroid
                if not (chacra or manzana):
                    self.stdout.write(self.style.WARNING(f"[chacra] Claves disponibles: {list(props.keys())[:20]}"))

                Building.objects.create(
                    barrio=(barrio or "").strip() or None,
                    chacra=(chacra or "").strip() or None,
                    manzana=(manzana or "").strip() or None,
                    numero=(numero or "").strip() or None,
                    letra=(letra or "").strip() or None,
                    escalera=(escalera or "").strip() or None,
                    geom=g,
                )        

        elif tipo == "chacra":
            for f in feats:
                props = props_dict_gdal(f) if mode == "gdal" else props_of(f)

                # Muchos datasets de chacras NO traen propiedades. Probamos y si no hay, usamos el FID.
                chacra = pick_value(props, ["CHACRA","chacra","NUM_CHACRA","NUMCHACRA"], ["chac"])
                manzana = None   # no corresponde en esta capa
                barrio  = pick_value(props, ["BARRIO","barrio"], ["barr"])

                if not chacra:
                    # Fallback seguro: usar FID como identificador de chacra
                    try:
                        chacra = str(getattr(f, "fid", None) or props.get("id") or props.get("ID"))
                    except Exception:
                        chacra = None  # si ni eso, queda null (igual guardamos el polígono)

                g = geom_of(f)
                g = to_multi(g, "MultiPolygon")

                BlockGrid.objects.create(
                    barrio=(barrio or "").strip() or None,
                    chacra=(chacra or "").strip() or None,
                    manzana=manzana,
                    geom=g,
                )

        elif tipo == "manzanero":
            for f in feats:
                props = props_dict_gdal(f) if mode == "gdal" else props_of(f)

                barrio  = pick_value(props, ["BARRIO","barrio"], ["barr"])
                chacra  = pick_value(props, ["CHACRA","chacra","CH","Ch"], ["chac"])
                manzana = pick_value(props, ["MANZANA","manzana","MZ","Mzna","Manz"], ["manz","mz"])

                g = geom_of(f)
                g = to_multi(g, "MultiPolygon")

                BlockGrid.objects.create(
                    barrio=(barrio or "").strip() or None,
                    chacra=(chacra or "").strip() or None,
                    manzana=(manzana or "").strip() or None,
                    geom=g,
                )

        elif tipo == "cuadricula":
            from validador.core.models import Parcel

            ok = 0
            for f in feats:
                # Propiedades: soporta GDAL (f.get) y JSON (dict)
                if hasattr(f, "get") and hasattr(f, "fields"):
                    # GDAL feature
                    props = {k: f.get(k) for k in f.fields}
                else:
                    # JSON feature: dict con 'properties'
                    props = props_of(f)  # tu helper que hace f.get("properties", {})
                    if not isinstance(props, dict):
                        props = {}

                g = geom_of(f)  # ya te devuelve GEOSGeometry con SRID=4326

                Parcel.objects.update_or_create(
                    gid=props.get("IDGIS"),
                    defaults={
                        "district": props.get("DISTRITO"),
                        "block":    props.get("MAN"),
                        "chacra":   props.get("CHA"),
                        "lot":      props.get("LOTE"),
                        "parcel":   props.get("PAR"),
                        "unit":     props.get("UNFU"),
                        "geom":     g,
                    },
                )
                ok += 1

            self.stdout.write(self.style.SUCCESS(f"Cuadrícula importada: {ok} filas"))





