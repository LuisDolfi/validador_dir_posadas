# validador/core/views.py
from django.http import JsonResponse
from validador.core.models import QueryLog
from django.shortcuts import render
from validador.core.services.address_validator import validate_address

def api_validate(request):
    q = request.GET.get("q", "").strip()
    return JsonResponse(validate_address(q))

def test_view(request):
    return render(request, "test.html")

def historial(request):
    rows = (QueryLog.objects
            .only("created_at","raw_text","normalized","quality","score")
            .order_by("-created_at")[:50])
    return render(request, "validador/historial.html", {"rows": rows})

def chat_ui(request):
    return render(request, "validador/chat.html")

# CRUD

from django.shortcuts import render, get_object_or_404, redirect
#from core.models import QueryLog
from django.contrib.auth.decorators import login_required

@login_required
def querylog_list(request):
    logs = QueryLog.objects.all().order_by('-created_at')[:100]
    return render(request, "validador/querylog_list.html", {"logs": logs})

@login_required
def querylog_detail(request, pk):
    log = get_object_or_404(QueryLog, pk=pk)
    return render(request, "validador/querylog_detail.html", {"log": log})

@login_required
def querylog_delete(request, pk):
    log = get_object_or_404(QueryLog, pk=pk)
    if request.method == "POST":
        log.delete()
        return redirect("core:querylog_list")
    return render(request, "validador/querylog_confirm_delete.html", {"log": log})

# Dashboard
# core/views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
import json

from validador.core.models import QueryLog


def _parse_range(request):
    rng = (request.GET.get("range") or "30d").lower()
    today = timezone.localdate()
    start, end = None, today

    if rng == "7d":
        start = today - timedelta(days=6)
    elif rng == "30d":
        start = today - timedelta(days=29)
    elif rng == "all":
        start = None
    elif rng == "custom":
        # ISO date yyyy-mm-dd
        f = request.GET.get("from") or ""
        t = request.GET.get("to") or ""
        try:
            start = datetime.fromisoformat(f).date() if f else None
        except ValueError:
            start = None
        try:
            end = datetime.fromisoformat(t).date() if t else today
        except ValueError:
            end = today
    else:
        # fallback
        rng = "30d"
        start = today - timedelta(days=29)

    return start, end, rng


@login_required
def dashboard(request):
    start, end, selected_range = _parse_range(request)

    qs = QueryLog.objects.all()
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)

    total = qs.count()
    by_status = qs.values("status").annotate(c=Count("id")).order_by("status")
    avg_score = qs.aggregate(avg=Avg("score"))["avg"] or 0

    logs_by_day = (
        qs.annotate(day=TruncDate("created_at"))
          .values("day")
          .annotate(count=Count("id"))
          .order_by("day")
    )

    ctx = {
        "total": total,
        "avg_score": round(avg_score, 2),
        "by_status": json.dumps(list(by_status)),
        "logs_by_day": json.dumps(list(logs_by_day), default=str),
        "selected_range": selected_range,
        "from": start.isoformat() if start else "",
        "to": end.isoformat() if end else "",
    }
    return render(request, "validador/dashboard.html", ctx)
from django.http import JsonResponse
from django.contrib.gis.db.models.functions import Transform

@login_required
def heatmap_data(request):
    # mismo parser de rango que usa el dashboard
    start, end, _ = _parse_range(request)

    qs = QueryLog.objects.all()
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)

    # Aseguramos WGS84 y sacamos lat/lng
    # (tu modelo ya está en 4326, pero Transform evita sorpresas)
    qs = qs.annotate(geom_wgs84=Transform("geom", 4326)).exclude(geom_wgs84=None)

    # weight: usá score si existe, si no 1.0
    payload = []
    for q in qs.iterator():
        lat = q.geom_wgs84.y
        lng = q.geom_wgs84.x
        w   = float(q.score or 1.0)
        payload.append([lat, lng, w])

    return JsonResponse({"points": payload})
