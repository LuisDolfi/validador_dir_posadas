# validacion/services.py
from django.db.models import Func, F
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.expressions import RawSQL
from validador.core.models import Street

class Unaccent(Func):
    function = "unaccent"

def buscar_via(nombre: str, tipo: str | None = None, top: int = 5):
    nombre = nombre.lower()
    base = Street.objects.all()
    if tipo in ("calle","avenida"):
        base = base.filter(kind=tipo)

    qs = (base
          .annotate(aliases_txt=RawSQL("array_to_string(ARRAY(SELECT x FROM jsonb_array_elements_text(aliases) x), ', ')", []))
          .annotate(sim_name=TrigramSimilarity(Unaccent('name'), nombre))
          .annotate(sim_alias=TrigramSimilarity(Unaccent('aliases_txt'), nombre))
          .annotate(sim=F('sim_name') + F('sim_alias')*0.9)
          .filter(sim__gt=0.30)
          .order_by('-sim')[:top])

    if not qs:
        qs = base.filter(name__icontains=nombre)[:top]
    return list(qs)

