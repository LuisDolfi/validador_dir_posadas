import re
import unicodedata

ABREVIATURAS = {
    "av": "avenida",
    "av.": "avenida",
    "c": "calle",
    "c.": "calle",
}

def normalizar(texto):
    """Convierte a minúsculas, quita tildes y espacios dobles."""
    texto = texto.strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def parsear(texto):
    """
    Devuelve un diccionario con los elementos detectados:
    tipo, via, via2, numero.
    """
    t = normalizar(texto)
    tokens = t.split()
    if tokens and tokens[0] in ABREVIATURAS:
        tokens[0] = ABREVIATURAS[tokens[0]]
    t = " ".join(tokens)

    m_altura = re.search(r'\b(\d{1,5})\b', t)
    numero = int(m_altura.group(1)) if m_altura else None
    base = re.sub(r'\b\d{1,5}\b', '', t).strip()

    if " y " in base:
        v1, v2 = [p.strip() for p in base.split(" y ", 1)]
        return {"tipo": None, "via": v1, "via2": v2, "numero": numero}

    tipo, nombre = None, base
    if base.startswith("avenida "):
        tipo, nombre = "avenida", base.replace("avenida ", "", 1).strip()
    elif base.startswith("calle "):
        tipo, nombre = "calle", base.replace("calle ", "", 1).strip()

    return {"tipo": tipo, "via": nombre, "numero": numero}
