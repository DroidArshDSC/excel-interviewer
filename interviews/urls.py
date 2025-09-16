# interviews/urls.py
from django.urls import path
from . import views_admin, views_candidate, views_reports

urlpatterns = [
    # Admin APIs
    path("api/admin/questions/generate", views_admin.generate_question),
    path("api/admin/packs", views_admin.create_pack),
    path("api/admin/assignments", views_admin.create_assignment),

    # Sonar health (admin only)
    path("api/admin/sonar/health", views_admin.sonar_health),

    # Candidate flow
    path("start/<uuid:assignment_id>", views_candidate.start_assignment),
    path("q/<uuid:assignment_id>/<uuid:question_id>", views_candidate.view_question),
    path("submit/", views_candidate.submit_answer),
    path("finish/<uuid:assignment_id>", views_candidate.finish_assignment),

    # Reports
    path("api/admin/assignments/<uuid:assignment_id>/report", views_reports.assignment_report),
]
