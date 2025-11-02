# validador/core/views.py
from django.http import JsonResponse
from django.shortcuts import render
from validador.core.services.address_validator import validate_address

def api_validate(request):
    q = request.GET.get("q", "").strip()
    return JsonResponse(validate_address(q))

def test_view(request):
    return render(request, "test.html")
