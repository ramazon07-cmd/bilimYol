import re
from collections import defaultdict

from django.core.management.base import BaseCommand

from apps.academics.models import Question


class Command(BaseCommand):
    help = "Qabul 2026 matematika javob kaliti holatini ko‘rsatadi"

    def handle(self, *args, **options):
        groups = defaultdict(
            lambda: {"total": 0, "configured": 0, "missing": []}
        )
        questions = Question.objects.filter(
            code__startswith="Q26-MATH-",
            subject__slug="math",
        ).order_by("code")

        for question in questions:
            match = re.match(
                r"^Q26-MATH-(.+)-(\d{2})$",
                question.code,
            )
            source = match.group(1) if match else "UNKNOWN"
            groups[source]["total"] += 1
            if question.accepted_text_answers.strip():
                groups[source]["configured"] += 1
            else:
                groups[source]["missing"].append(question.code)

        total = 0
        configured = 0
        for source in [
            "G2", "G3", "G4", "G5",
            "G6", "G7", "G8-9", "G10-11",
        ]:
            data = groups[source]
            total += data["total"]
            configured += data["configured"]
            self.stdout.write(
                f"{source}: {data['configured']}/{data['total']}"
            )
            if data["missing"]:
                self.stdout.write(
                    "  Yetishmaydi: "
                    + ", ".join(data["missing"][:10])
                )

        self.stdout.write(
            self.style.SUCCESS(f"Jami: {configured}/{total}")
        )
