from typing import Optional
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
from .models import Submission, Assignment, Question, Grade
from .services import sonar_reasoning
from .services import storage as storage_service  # optional: to create signed URLs if bucket is private
from .utils import make_json_safe


@csrf_exempt
@require_http_methods(["POST"])
def start_assignment(request, assignment_id: uuid.UUID):
    """Mark assignment as started (stub)."""
    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponseBadRequest("Invalid assignment id")

    # In a real flow you could set assignment.started_at = timezone.now()
    return JsonResponse({
        "ok": True,
        "assignment_id": assignment.id,
        "candidate": assignment.candidate.name,
        "pack": assignment.pack.name,
    })


def view_question(request, assignment_id: uuid.UUID, question_id: uuid.UUID):
    """Fetch question details for candidate."""
    try:
        assignment = Assignment.objects.get(id=assignment_id)
        question = Question.objects.get(id=question_id)
    except (Assignment.DoesNotExist, Question.DoesNotExist):
        return HttpResponseBadRequest("Invalid ids")

    return JsonResponse({
        "ok": True,
        "assignment_id": assignment.id,
        "question": {
            "id": question.id,
            "title": question.title,
            "spec": question.spec,
            "rubric": question.rubric,
            "qtype": question.qtype,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def submit_answer(request):
    """
    Judge-only submit endpoint (JSON).
    Expected body:
      {"assignment_id":"<uuid>", "question_id":"<uuid>", "answer": ..., "file_url": "..."}
    """
    # parse JSON
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    assignment_id = payload.get("assignment_id")
    question_id = payload.get("question_id")
    answer = payload.get("answer")
    file_url = payload.get("file_url")

    if not (assignment_id and question_id):
        return HttpResponseBadRequest("assignment_id and question_id required")

    try:
        assignment = Assignment.objects.get(id=assignment_id)
        question = Question.objects.get(id=question_id)
    except (Assignment.DoesNotExist, Question.DoesNotExist):
        return HttpResponseBadRequest("Invalid assignment or question id")

    # Persist submission
    submission = Submission.objects.create(
        assignment=assignment,
        question=question,
        answer=answer if answer is not None else {},
        file_url=file_url or None,
    )

    # (optional) signed URL generation
    sonar_file_url = None
    if submission.file_url:
        try:
            sonar_file_url = storage_service.generate_signed_url(submission.file_url, expires_in=300)
        except Exception:
            sonar_file_url = submission.file_url

    # Build JSON-safe payloads for Sonar
    question_payload = make_json_safe({
        "id": question.id,
        "title": question.title,
        "spec": question.spec or {},
        "rubric": question.rubric or {},
    })
    submission_payload = make_json_safe({
        "submission_id": submission.id,
        "answer": submission.answer,
        "file_url": sonar_file_url or submission.file_url,
        "created_at": getattr(submission, "created_at", None),
    })

    # Call Sonar-reasoning judge
    try:
        judge_result = sonar_reasoning.judge_answer(question_payload, submission_payload, None)
    except Exception as e:
        judge_result = {
            "score": 0,
            "verdict": "error",
            "mistakes": [],
            "improvements": [f"judge_error: {e}"],
            "citations": []
        }

    # sanitize judge_result before persisting/returning
    safe_judge = make_json_safe(judge_result)

    # Final score = judge-only
    final_score = float(safe_judge.get("score", 0) or 0)

    # Persist Grade
    grade = Grade.objects.create(
        submission=submission,
        judge=safe_judge,
        score=final_score,
    )

    # Build response
    response = {
        "ok": True,
        "submission_id": str(submission.id),
        "grade_id": str(grade.id),
        "score": final_score,
        "runner": None,
        "judge": safe_judge,
        "file_url": submission.file_url,
    }

    # Strip debug from judge in production
    if not settings.DEBUG and isinstance(response.get("judge"), dict):
        response["judge"].pop("debug", None)

    return JsonResponse(response)


@csrf_exempt
@require_http_methods(["POST"])
def finish_assignment(request, assignment_id: uuid.UUID):
    """Mark assignment as finished (stub)."""
    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponseBadRequest("Invalid assignment id")

    # In a real flow: assignment.finished_at = timezone.now()
    return JsonResponse({
        "ok": True,
        "assignment_id": assignment.id,
        "status": "finished"
    })
