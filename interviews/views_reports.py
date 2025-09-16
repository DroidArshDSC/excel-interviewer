# interviews/views_reports.py
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from .models import Assignment, Submission, Grade

@csrf_exempt
@require_http_methods(["GET"])
def assignment_report(request, assignment_id: int):
    try:
        assignment = Assignment.objects.get(id=assignment_id)
    except Assignment.DoesNotExist:
        return HttpResponseBadRequest("Invalid assignment id")

    submissions = Submission.objects.filter(assignment=assignment).order_by("created_at")
    grades = Grade.objects.filter(submission__in=submissions)

    avg_score = grades.aggregate(avg=Avg("score"))["avg"] or 0.0

    submissions_out = []
    for sub in submissions:
        # safe lookup for grade (returns None if absent)
        grade = Grade.objects.filter(submission=sub).first()

        # if you want runner/judge details, include them only when grade exists
        runner = grade.runner if grade else None
        judge = grade.judge if grade else None
        score = grade.score if grade else None

        submissions_out.append({
            "submission_id": sub.id,
            "question_id": sub.question.id if sub.question else None,
            "question_title": sub.question.title if sub.question else None,
            "answer": sub.answer,
            "score": score,
            "runner": runner,
            "judge": judge,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
        })

    report = {
        "ok": True,
        "assignment_id": assignment.id,
        "candidate": {
            "id": assignment.candidate.id,
            "name": assignment.candidate.name,
            "email": assignment.candidate.email,
        },
        "pack": {"id": assignment.pack.id, "name": assignment.pack.name} if assignment.pack else None,
        "average_score": avg_score,
        "submissions": submissions_out,
    }

    return JsonResponse(report, safe=False)
