from django.contrib import admin
from .models import Candidate, Question, Pack, PackItem, Assignment, Submission, Grade


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email")
    search_fields = ("name", "email")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "qtype", "version")
    list_filter = ("qtype", "version")
    search_fields = ("title",)


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "version")
    search_fields = ("name",)


@admin.register(PackItem)
class PackItemAdmin(admin.ModelAdmin):
    list_display = ("id", "pack", "question", "timer_seconds")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate", "pack", "started_at", "finished_at")
    list_filter = ("pack",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "assignment", "question", "created_at")


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "score")
    list_filter = ("score",)
