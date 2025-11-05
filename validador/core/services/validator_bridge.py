# validador/core/services/validator_bridge.py
from rest_framework.test import APIRequestFactory
from validacion.views import ValidateAddress
from .llm_service import craft_reply

def ask_vadi(message, val_json):
    return craft_reply(message, val_json)

def run_validator(texto, user=None):
    """
    Ejecuta la misma lógica de ValidateAddress (DRF) y devuelve su JSON.
    No exponemos clave ni hacemos HTTP; llama a la vista internamente.
    """
    factory = APIRequestFactory()
    req = factory.post("/validar/", {"texto": texto}, format="json")
    if user:
        req.user = user
    resp = ValidateAddress.as_view()(req)
    return getattr(resp, "data", {})  # {'status': ..., 'opciones': ...} + lo que ya retornás
