from django.contrib import admin
from .models import QueryLog, Street

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at","status", "normalized", "score", "quality", "user", "street", "building", "short_payload")
    list_filter = ("status","quality","user","created_at")
    search_fields = ("raw_text","normalized", "llm_reason", "user__username")

# método auxiliar para mostrar un resumen del JSON
    def short_payload(self, obj):
        data = obj.result_json or {}
        # Mostramos hasta ~80 chars para no romper el layout
        s = str(data)
        return (s[:77] + "…") if len(s) > 80 else s
    short_payload.short_description = "payload"
    
@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = ("id","kind","name")
    search_fields = ("name",)
    list_filter = ("kind",)