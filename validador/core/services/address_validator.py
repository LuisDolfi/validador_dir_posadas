import re
from validador.core.models import Street, BlockGrid, Building
from django.contrib.gis.measure import D

CALLE_ALTURA_RE = re.compile(r"^\s*([A-Za-zÁÉÍÓÚÑñáéíóú\s\.]+?)\s+(\d{1,6})\s*$")

def validate_address(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"query": text, "status": "error", "sugerencia": "Falta la dirección."}

    # 1) Cruce: "Lavalle y Bustamante"
    parts_y = [p for p in text.replace(",", " ").split() if p.lower() != "y"]
    if " y " in text.lower() and len(parts_y) >= 2:
        s1 = Street.objects.filter(name__icontains=parts_y[0]).first()
        s2 = Street.objects.filter(name__icontains=parts_y[1]).first()
        if s1 and s2 and s1.geom and s2.geom and s1.geom.intersects(s2.geom):
            inter = s1.geom.intersection(s2.geom)
            p = inter.centroid if inter.geom_type != "Point" else inter
            zona = BlockGrid.objects.filter(geom__contains=p).first()
            hay_mono = Building.objects.filter(geom__distance_lte=(p, D(m=120))).exists()
            return {
                "query": text,
                "status": "incompleta" if hay_mono else "valida",
                "contexto": {
                    "chacra": getattr(zona, "chacra", None),
                    "manzana": getattr(zona, "manzana", None),
                    "zona_monoblock": hay_mono,
                    "centroid": list(p.coords) if hasattr(p, "coords") else None,
                },
                "sugerencia": "Zona de monoblocks: indique edificio/torre, escalera y depto."
                              if hay_mono else None,
            }

    # 2) Calle + altura: "Lavalle 1234"
    m = CALLE_ALTURA_RE.match(text)
    if m:
        calle_txt, altura = m.group(1).strip(), m.group(2)
        s = Street.objects.filter(name__icontains=calle_txt).first()
        if s:
            # Sin rangos oficiales: no podemos verificar ese número.
            # Damos válida-parcial y pedimos entrecalles o barrio.
            # Si es zona monoblock, pedimos torre/escalera/depto.
            p = s.geom.centroid  # marcador aproximado (sin usar la altura)
            zona = BlockGrid.objects.filter(geom__contains=p).first()
            hay_mono = Building.objects.filter(geom__distance_lte=(p, D(m=120))).exists()
            sugerencia = ("Dirección con altura, pero sin rangos oficiales. "
                          "Indique entrecalles o barrio/chacra para afinar.")
            if hay_mono:
                sugerencia += " Zona de monoblocks: indique edificio/torre, escalera y depto."
            return {
                "query": text,
                "status": "valida_sin_rango",
                "contexto": {
                    "calle_detectada": s.name,
                    "altura": altura,
                    "chacra": getattr(zona, "chacra", None),
                    "manzana": getattr(zona, "manzana", None),
                    "zona_monoblock": hay_mono,
                    "centroid": list(p.coords) if hasattr(p, "coords") else None,
                },
                "sugerencia": sugerencia,
            }

    # 3) Sugerencias si no encaja en los casos anteriores
    base = parts_y[0] if parts_y else text
    matches = list(Street.objects.filter(name__icontains=base).values_list("name", flat=True)[:8])
    return {
        "query": text,
        "status": "ambigua" if matches else "no_encontrada",
        "sugerencia": "Especifique altura o cruce. Si es barrio con chacras/manzanas, indique edificio/torre.",
        "coincidencias": matches,
    }
