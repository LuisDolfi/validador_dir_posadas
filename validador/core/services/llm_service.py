# services/llm_service.py
from openai import OpenAI
import os
import random

client = None
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    client = None  # si no hay clave, seguimos en modo offline

SYSTEM_PROMPT = (
    "Sos VADI, un asistente que valida direcciones en Posadas, Misiones. "
    "Respondé corto y claro."
)

def craft_reply(user_text: str, val_json: dict) -> str:
    """
    Genera respuesta con LLM o simula si no hay crédito/Internet.
    """
    try:
        if client:
            content = f"Entrada: {user_text}\nResultado: {val_json}"
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                temperature=0.3,
                max_tokens=150,
            )
            return completion.choices[0].message.content.strip()
        else:
            raise Exception("offline")

    except Exception as e:
        print(f"⚠️ Error en craft_reply: {e}")
        # --- Simulación local ---
        respuestas = [
            f"Dirección procesada: {val_json.get('normalized','(sin normalizar)') or user_text}",
            "Parece válida. ¿Querés que la confirme en el mapa?",
            "No encontré coincidencias exactas, pero podría ser una variante conocida.",
            "Te entiendo, pero necesito el número o manzana para precisar la ubicación.",
        ]
        return random.choice(respuestas)
