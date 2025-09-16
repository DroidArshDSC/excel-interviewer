# interviews/views_admin.py
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import Pack, Candidate, Assignment
from .services import sonar_reasoning

@csrf_exempt
@require_POST
def generate_question(request):
    admin_prompt = request.POST.get("prompt") or "Default Excel interview question"
    return JsonResponse({
        "ok": True,
        "question": {
            "title": "stub",
            "prompt": admin_prompt
        }
    })

@csrf_exempt
@require_POST
def create_pack(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    name = payload.get("name", "Unnamed Pack")
    version = payload.get("version", 1)

    pack = Pack.objects.create(name=name, version=version)
    return JsonResponse({"ok": True, "pack_id": pack.id})

@csrf_exempt
@require_POST
def create_assignment(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    candidate_id = payload.get("candidate_id")
    pack_id = payload.get("pack_id")

    if not candidate_id or not pack_id:
        return HttpResponseBadRequest("candidate_id and pack_id required")

    try:
        candidate = Candidate.objects.get(id=candidate_id)
        pack = Pack.objects.get(id=pack_id)
    except (Candidate.DoesNotExist, Pack.DoesNotExist):
        return HttpResponseBadRequest("Invalid candidate_id or pack_id")

    assignment = Assignment.objects.create(candidate=candidate, pack=pack)
    return JsonResponse({"ok": True, "assignment_id": assignment.id})

@staff_member_required
def sonar_health(request):
    """
    Admin-only Sonar health check endpoint.
    Returns JSON: {"ok": bool, "info": {...}}
    """
    ok, info = sonar_reasoning.ping()
    return JsonResponse({"ok": ok, "info": info})
