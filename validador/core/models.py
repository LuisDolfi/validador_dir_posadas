from django.db import models

# Create your models here.
from django.contrib.gis.db import models

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
