import uuid
from django.core.management.base import BaseCommand
from interviews.models import Candidate, Pack, PackItem, Question, Assignment


class Command(BaseCommand):
    help = "Seed demo Candidate, Pack, Question, and Assignment with UUIDs"

    def handle(self, *args, **options):
        # Create candidate
        candidate, _ = Candidate.objects.get_or_create(
            email="demo@example.com",
            defaults={"name": "Demo User"},
        )

        # Create question
        q, _ = Question.objects.get_or_create(
            title="VLOOKUP concept",
            qtype="theory",
            defaults={
                "spec": {"prompt": "Explain VLOOKUP vs INDEX/MATCH."},
                "rubric": {
                    "key_points": ["lookup mechanics", "limitations", "alternatives"]
                },
            },
        )

        # Create pack
        pack, _ = Pack.objects.get_or_create(name="Starter Pack")

        # Add question to pack
        PackItem.objects.get_or_create(pack=pack, question=q)

        # Create assignment
        assignment, _ = Assignment.objects.get_or_create(candidate=candidate, pack=pack)

        self.stdout.write(self.style.SUCCESS("✅ Demo data seeded"))
        self.stdout.write(f"Candidate UUID: {candidate.id}")
        self.stdout.write(f"Question UUID: {q.id}")
        self.stdout.write(f"Assignment UUID: {assignment.id}")
