from django.contrib import admin
from validador.core.models import Street, BlockGrid, Building, Parcel, QueryLog

@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = ("id","kind","name")
    list_filter = ("kind",)
    search_fields = ("name",)

@admin.register(BlockGrid)
class BlockGridAdmin(admin.ModelAdmin):
    list_display = ("id","chacra","manzana")
    search_fields = ("chacra","manzana")

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("id","barrio","chacra","manzana","numero","letra","escalera")
    search_fields = ("barrio","chacra","manzana","numero","letra","escalera")

@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ("id","chacra","manzana","lote")
    search_fields = ("chacra","manzana","lote")

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ("created_at","user","result","raw_text","street","building")
    list_filter = ("result","created_at")
    search_fields = ("raw_text",)

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "raw_text", "normalized", "quality")
    list_filter = ("quality",)
    search_fields = ("raw_text","normalized")
