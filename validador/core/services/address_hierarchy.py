import re
from validador.core.models import BlockGrid, Building

def buscar_zona_interna(parsed):
    """
    Busca direcciones basadas en chacra/manzana/casa o edificio.
    """
    q = parsed.get("via", "").lower()

    if "chacra" in q:
        num = re.search(r'\d+', q)
        if num:
            return BlockGrid.objects.filter(chacra=num.group(0))

    if "monoblock" in q or "edificio" in q:
        num = re.search(r'\d+', q)
        if num:
            return Building.objects.filter(numero=num.group(0))

    return []
