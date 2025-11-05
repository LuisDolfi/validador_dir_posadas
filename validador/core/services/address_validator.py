import re
from validador.core.models import Street, BlockGrid, Building, QueryLog
from django.contrib.gis.measure import D
#from .llm_service import normalize_address_with_llm


CALLE_ALTURA_RE = re.compile(r"^\s*([A-Za-zÁÉÍÓÚÑñáéíóú\s\.]+?)\s+(\d{1,6})\s*$")

def validate_address(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"query": text, "status": "error", "sugerencia": "Falta la dirección."}

            
    # LLM + logging para otros casos

def validate_address(text: str) -> dict:
    # 1) normalización con LLM
    llm_result = normalize_address_with_llm(text)
    normalized = llm_result["normalized"]
    reason = llm_result["reason"]

        # 2) ... tu matching usando `normalized` ...
        #    calculás: result (dict con todo), score (float), quality ('A','M','B')

    result = {  # ejemplo mínimo; dejá tu estructura real
        "input": text,
        "normalized": normalized,
        "reason": reason,
        "tipo": "altura|interseccion|otro",
        "match": { "street_a": "...", "street_b": None, "number": 1234 },
        "geom": { "lat": -27.45, "lon": -55.88 },
    }
    score = 0.86
    quality = "M"

        # 3) Persistencia en QueryLog
    try:
        QueryLog.objects.create(
            raw_text=text,
            normalized=normalized,
            llm_reason=reason,
            status=result,
            score=score,
            quality=quality,
        )
    except Exception as e:
        # no bloquees el flujo si falla la DB
        pass
    
        

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
    parts_y = []  # partes de la dirección (si no se detectaron antes, queda vacío)
    base = parts_y[0] if parts_y else text
    matches = list(Street.objects.filter(name__icontains=base).values_list("name", flat=True)[:8])
    result = {
        "query": text,
        "status": "ambigua" if matches else "no_encontrada",
        "sugerencia": "Especifique altura o cruce. Si es barrio con chacras/manzanas, indique edificio/torre.",
        "coincidencias": matches,
    }
    return result