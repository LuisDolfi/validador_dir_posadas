from rest_framework import serializers
from .models import QueryLog

class QueryLogSerializer(serializers.ModelSerializer):
    # Campos derivados (opcionales) para que el JSON sea cómodo
    status = serializers.SerializerMethodField()
    match = serializers.SerializerMethodField()

    class Meta:
        model = QueryLog
        fields = [
            "id", "created_at",
            "raw_text", "normalized", "llm_reason",
            "result", "status", "match",
            "score", "quality",
        ]
        read_only_fields = ["id", "created_at", "result", "status", "match", "score", "quality"]

    def get_status(self, obj):
        try:
            return (obj.result or {}).get("status")
        except Exception:
            return None

    def get_match(self, obj):
        try:
            return (obj.result or {}).get("match") or (obj.result or {}).get("coincidencias")
        except Exception:
            return None


# Si querés un endpoint que reciba SOLO el texto y procese:
class ValidateAddressInputSerializer(serializers.Serializer):
    raw_text = serializers.CharField(max_length=240)
