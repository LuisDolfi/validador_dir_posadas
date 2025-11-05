# core/api.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from .models import QueryLog
from .serializers import QueryLogSerializer, ValidateAddressInputSerializer
from validador.core.services.address_validator import validate_address
from rest_framework.permissions import IsAuthenticated
# chat endpoint con LLM
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .services.llm_service import craft_reply
from .services.validator_bridge import run_validator
import json

@csrf_exempt
def chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body or "{}")
        user_text = (data.get("message") or "").strip()
        if not user_text:
            return JsonResponse({"error": "Mensaje vacío"}, status=400)

        # 1) Validar dirección con tu lógica existente
        val_json = run_validator(user_text, user=request.user if request.user.is_authenticated else None)

        # 2) Redactar respuesta con el LLM
        answer = craft_reply(user_text, val_json)

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        # si pasa algo antes de loguear, devolvemos 500
        print(f"⚠️ Error en chat(): {e}")
        return JsonResponse({"error": str(e)}, status=500)

    # 3) Registrar QueryLog (NO bloquear la respuesta si falla el insert)
    try:
        QueryLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            raw_text=user_text,
            parsed_tokens={},                                  # si aún no generás tokens
            status=val_json.get("status", ""),
            result_json=val_json,                              # JSON completo del validador
            normalized=val_json.get("normalized", "") or "",   # fallback vacío
            llm_reason=answer,                                 # lo que “dijo” VADI
            score=0.0,
            quality="",                                        # A/M/B si luego lo calculás
        )
    except Exception as log_err:
        # no romper la UX si falló el log
        print(f"⚠️ No se pudo guardar QueryLog: {log_err}")

    # 4) Responder al frontend
    return JsonResponse({"response": answer, "validator": val_json})

class QueryLogViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
class QueryLogViewSet(ModelViewSet):
    """
    CRUDL de validaciones.
    POST puede aceptar:
      - payload completo (ya creado)  -> crea directo
      - {"raw_text": "..."}           -> ejecuta validate_address() y persiste
    """
    queryset = QueryLog.objects.all().order_by("-created_at")
    serializer_class = QueryLogSerializer
    filterset_fields = ["quality"]
    search_fields = ["raw_text", "normalized"]

    def create(self, request, *args, **kwargs):
        # Si viene solo raw_text, procesamos con tu pipeline
        input_ser = ValidateAddressInputSerializer(data=request.data)
        if input_ser.is_valid():
            text = input_ser.validated_data["raw_text"].strip()
            result = validate_address(text)

            # Persistimos (si tu validate_address no lo hizo)
            # Si ya lo hace adentro, podrías buscar el último registro por raw_text+created_at.
            obj = QueryLog.objects.create(
                raw_text=text,
                normalized=result.get("normalized", text),
                llm_reason=result.get("reason", ""),
                result=result,
                score=result.get("score"),
                quality=result.get("quality"),
            )
            return Response(QueryLogSerializer(obj).data, status=status.HTTP_201_CREATED)

        # Si no era el formato simple, probamos crear con el serializer del modelo
        return super().create(request, *args, **kwargs)
