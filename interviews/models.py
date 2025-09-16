from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Candidate(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=120)
    # For MVP we won’t implement full auth, just store a placeholder hash
    password_hash = models.CharField(max_length=256, blank=True, default="")

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    QTYPE_CHOICES = (("theory", "Theory"), ("practical", "Practical"))
    title = models.CharField(max_length=200)
    qtype = models.CharField(max_length=16, choices=QTYPE_CHOICES)
    spec = models.JSONField(default=dict)       # prompt/dataset/task spec
    rubric = models.JSONField(default=dict)     # grading rubric
    dataset = models.JSONField(default=dict, blank=True, null=True)
    ideal_answer = models.TextField(blank=True, default="")
    version = models.IntegerField(default=1)

    def __str__(self):
        return f"[{self.qtype}] {self.title} v{self.version}"


class Pack(models.Model):
    name = models.CharField(max_length=120)
    version = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.name} v{self.version}"


class PackItem(models.Model):
    pack = models.ForeignKey(Pack, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    timer_seconds = models.IntegerField(
        default=180, validators=[MinValueValidator(10)]
    )


class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    pack = models.ForeignKey(Pack, on_delete=models.CASCADE)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.JSONField(default=dict)          # keep existing JSON/text answer
    file_url = models.TextField(blank=True, null=True)  # stores Supabase public or signed URL
    created_at = models.DateTimeField(default=timezone.now)


class Grade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE)
    #runner = models.JSONField(null=True, blank=True)   # deterministic checks
    judge = models.JSONField(default=dict)    # Sonar-reasoning result
    score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
