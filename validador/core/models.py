from django.db import models
# Create your models here.
from django.contrib.gis.db import models
# Preferí el de GIS; si no está, caemos al de Postgres
#try:
#    from django.contrib.gis.db.models.indexes import GistIndex
#except ModuleNotFoundError:
from django.contrib.postgres.indexes import GistIndex
from django.conf import settings

class Parcel(models.Model):
    # Códigos catastrales del JSON de IDE Posadas
    district = models.CharField(max_length=50, null=True, blank=True)   # DISTRITO
    section  = models.CharField(max_length=10, null=True, blank=True)   # SEC / SECCION (si existiera)
    block    = models.CharField(max_length=10, null=True, blank=True)   # MAN
    lot      = models.CharField(max_length=10, null=True, blank=True)   # LOTE
    chacra   = models.CharField(max_length=10, null=True, blank=True)
    parcel   = models.CharField(max_length=10, null=True, blank=True)   # PAR
    unit     = models.CharField(max_length=10, null=True, blank=True)   # UNFU
    gid      = models.CharField(max_length=64, unique=True)             # IDGIS
    geom     = models.MultiPolygonField(srid=4326)

    class Meta:
        indexes = [GistIndex(fields=["geom"])]
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"

    def __str__(self):
        return f"Parcela {self.block}-{self.lot} ({self.gid})"

# --- 1. Calles y Avenidas ---
class Street(models.Model):
    KIND_CHOICES = (
        ('calle', 'Calle'),
        ('avenida', 'Avenida'),
    )
    name = models.CharField(max_length=100, db_index=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    aliases = models.JSONField(default=list, blank=True)
    geom = models.MultiLineStringField(srid=4326)  # Coordenadas WGS84

    def __str__(self):
        return f"{self.kind.title()} {self.name}"


# --- 2. Chacras y Manzanas ---
class BlockGrid(models.Model):
    barrio = models.CharField(max_length=100, blank=True, null=True)
    chacra = models.CharField(max_length=20, blank=True, null=True)
    manzana = models.CharField(max_length=20, blank=True, null=True)
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return f"Chacra {self.chacra or '-'} / Manzana {self.manzana or '-'}"


# --- 3. Edificios y Monoblocks ---
class Building(models.Model):
    barrio = models.CharField(max_length=100, blank=True, null=True)
    chacra = models.CharField(max_length=20, blank=True, null=True)
    manzana = models.CharField(max_length=20, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    letra = models.CharField(max_length=5, blank=True, null=True)
    escalera = models.CharField(max_length=5, blank=True, null=True)
    geom = models.PointField(srid=4326)

    def __str__(self):
        return f"Edificio {self.numero or '?'}{self.letra or ''} (Ch {self.chacra})"


# --- 4. Direcciones validadas / normalizadas ---
class Address(models.Model):
    raw_input = models.CharField(max_length=255)
    normalized_text = models.CharField(max_length=255, blank=True, null=True)
    block = models.ForeignKey(BlockGrid, on_delete=models.SET_NULL, null=True, blank=True)
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True)
    geom = models.PointField(srid=4326, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.normalized_text or self.raw_input

# --- 5. Registro de consultas al Validador de Direcciones ---
# Esta clase guarda cada intento de validación realizado por el usuario,
# junto con el texto ingresado, los tokens extraídos, el resultado
# (OK / AMBIGUA / INCOMPLETA / NO_MATCH), y el punto geográfico asociado.
# Se usa luego para alimentar el Dashboard de uso y estadísticas.


class QueryLog(models.Model):
    RESULT_CHOICES = [
        ("OK", "OK"),                   # Dirección encontrada con éxito
        ("AMBIGUA", "AMBIGUA"),         # Dirección encontrada con éxito
        ("INCOMPLETA", "INCOMPLETA"),   # Dirección encontrada con éxito
        ("NO_MATCH", "NO_MATCH"),       # No se encontró coincidencia
    ]
    # Usuario que hizo la consulta (opcional)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    # Texto tal cual fue ingresado por el usuario
    raw_text = models.TextField(blank=True, default="")
    # Tokens o estructura interpretada por el parser
    parsed_tokens = models.JSONField(default=dict, blank=True)
    # Relación con una calle/avenida y edificio, si corresponde
    status = models.CharField(max_length=12, choices=RESULT_CHOICES)
    street = models.ForeignKey(Street, on_delete=models.SET_NULL, null=True, blank=True)
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True)
    # Coordenadas del punto de validación
    geom = models.PointField(srid=4326, null=True, blank=True)
    # Fecha y hora de creación
    created_at = models.DateTimeField(auto_now_add=True)
    # 👇 nuevos
    normalized = models.CharField(max_length=240, blank=True, default="")
    llm_reason = models.TextField(blank=True, default="")      # explicación del LLM
    result_json = models.JSONField(default=dict, blank=True)         # lo que devuelve validate_address()
    score = models.FloatField(null=True, blank=True, default=0)            # opcional
    quality = models.CharField(max_length=1, blank=True)        # 'A'/'M'/'B'


    def __str__(self):
        return f"[{self.status}] {self.raw_text[:40]}"
