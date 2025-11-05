from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from validador.core.services.address_hierarchy import buscar_zona_interna
from validador.core.models import QueryLog, Street, Building, BlockGrid  # para type hints y log
from .parser import parsear
from .services import buscar_via
from django.shortcuts import render, redirect
from django.contrib import messages
from validador.core.services.address_validator import validate_address
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.views import LoginView, LogoutView

class VadiLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        # 1) Si vino con ?next=... respetalo
        nxt = self.get_redirect_url()
        if nxt:
            return nxt
        # 2) Si es admin/staff -> admin
        if self.request.user.is_staff or self.request.user.is_superuser:
            return "/admin/"
        # 3) Usuario común -> validador
        return reverse("validacion:usuario")
@login_required
def post_login_redirect(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("/admin/")
    return redirect("validacion:usuario")
# importa TU validador (ajustá el import según tu árbol real)
try:
    from validador.core.services.address_validator import validate_address
except ModuleNotFoundError:
    # fallback si lo tenés como validador/core/address_validator.py
    from validador.core.services.address_validator import validate_address

# mapeo de estados del validador -> QueryLog.RESULT_CHOICES
MAP_RESULT = {
    "valida": "OK",
    "valida_sin_rango": "INCOMPLETA",
    "incompleta": "INCOMPLETA",
    "ambigua": "AMBIGUA",
    "no_encontrada": "NO_MATCH",
    "error": "NO_MATCH",
}

# === Vistas de interfaz web ===
def landing(request):
    return render(request, "validador/landing.html")

def validador_usuario(request):
    context = {}
    if request.method == "POST":
        raw = (request.POST.get("direccion") or "").strip()
        if not raw:
            messages.warning(request, "Ingresá una dirección.")
            return redirect("validacion:usuario")
        try:
            result = validate_address(raw)
            context["result"] = result
        except Exception as e:
            messages.error(request, f"Error al validar: {e}")
    return render(request, "validador/usuario.html", context)

def historial(request):
    q = QueryLog.objects.order_by("-created_at")[:50]
    return render(request, "validador/historial.html", {"rows": q})

# === API REST ===
class ValidateAddress(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        texto = (request.data.get("input") or "").strip()
        parsed = parsear(texto)

        # --- 1) PRUEBA NORMAL: buscar vía (calle/avenida) ---
        cand1 = buscar_via(parsed.get("via", ""), parsed.get("tipo"))
        status = "NO_MATCH"
        payload = {"status": status, "input": texto, "parsed": parsed, "candidatos": []}
        geom_pt = None
        street_fk = None
        building_fk = None
        razon_llm = ""   #  TODO: explicación textual generada por el LLM (por ahora vacía)
        score = 0.0      #  TODO: puntaje de confianza (por ahora neutro)
        quality = ""     #  TODO: clasificación 'A'/'M'/'B' (por ahora vacío)

        if parsed.get("via2"):
            # esquina -> dejamos INCOMPLETA salvo que más adelante quieras intersección exacta
            cand2 = buscar_via(parsed["via2"])
            if cand1 and cand2:
                status = "INCOMPLETA"
                payload = {"status": status,
                           "pregunta": f"¿Es la esquina entre {cand1[0].name} y {cand2[0].name}? ¿Tenés altura?"}
        elif cand1:
            # tenemos calle/avenida, si hay altura damos OK (interpolado)
            street_fk = cand1[0]
            if parsed.get("numero"):
                status = "OK"
                payload = {
                    "status": status,
                    "via": cand1[0].name,
                    "tipo": cand1[0].kind,
                    "altura": parsed["numero"],
                    "precision": "interpolada",
                }
            else:
                status = "INCOMPLETA"
                payload = {"status": status, "pregunta": "¿Tenés la altura o una esquina cercana?"}

        # --- 2) FALLBACK JERÁRQUICO: chacra/manzana/monoblock ---
        # Se dispara si NO hubo match de calle/avenida (o si el texto sugiere zona interna)
        texto_l = texto.lower()
        sugiere_zona_interna = any(k in texto_l for k in ("chacra", "manzana", "monoblock", "edificio", "torre"))
        if (status == "NO_MATCH") or (sugiere_zona_interna and parsed.get("via") and not cand1):
            qs = list(buscar_zona_interna(parsed))

            if len(qs) == 1:
                obj = qs[0]
                # Elegimos un punto representativo
                geom = getattr(obj, "geom", None)
                if geom:
                    point = geom if geom.geom_type == "Point" else geom.centroid
                    geom_pt = point
                    lon, lat = point.x, point.y
                else:
                    lon = lat = None

                if isinstance(obj, Building):
                    status = "OK"
                    building_fk = obj
                    payload = {
                        "status": status,
                        "precision": "edificio",
                        "detalle": {
                            "barrio": getattr(obj, "barrio", None),
                            "chacra": getattr(obj, "chacra", None),
                            "manzana": getattr(obj, "manzana", None),
                            "numero": getattr(obj, "numero", None),
                            "letra": getattr(obj, "letra", None),
                            "escalera": getattr(obj, "escalera", None),
                            "centro": {"lon": lon, "lat": lat},
                        }
                    }
                elif isinstance(obj, BlockGrid):
                    status = "INCOMPLETA"
                    payload = {
                        "status": status,
                        "precision": "zona_interna",
                        "detalle": {
                            "chacra": getattr(obj, "chacra", None),
                            "manzana": getattr(obj, "manzana", None),
                            "centro": {"lon": lon, "lat": lat},
                        },
                        "pregunta": "¿Podés indicar la casa/torre/escalera?"
                    }
            elif len(qs) > 1:
                status = "AMBIGUA"
                opciones = []
                for o in qs[:8]:
                    if isinstance(o, Building):
                        opciones.append(f"Edificio (chacra {getattr(o,'chacra',None)}, manzana {getattr(o,'manzana',None)}, nro {getattr(o,'numero',None)})")
                    elif isinstance(o, BlockGrid):
                        opciones.append(f"Chacra {getattr(o,'chacra',None)}, manzana {getattr(o,'manzana',None)}")
                payload = {"status": status, "opciones": opciones, "pregunta": "¿Cuál de estas opciones es la correcta?"}

        # --- 3) Registrar QueryLog ---
        QueryLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            raw_text=texto,
            parsed_tokens=parsed,
            status=status,
            result_json=payload,           # ← el JSON completo
            llm_reason=razon_llm or "",
            score=score or 0,
            quality=quality or "",
            street=street_fk,
            building=building_fk,
            geom=geom_pt  # Point en SRID 4326 (tus modelos ya están así)
        )

        return Response(payload, status=200)

class LogoutGetView(LogoutView):
    
    """
    Versión extendida de LogoutView que permite GET para simplificar
    el botón 'Salir' en el header sin usar formularios POST.
    """
    
    http_method_names = ["get", "post", "head", "options"]

    def get(self, request, *args, **kwargs):
        # reutiliza la lógica del POST
        return self.post(request, *args, **kwargs)

