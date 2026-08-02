import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.academics.models import Question


def split_alternatives(value: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"\|\||\r?\n", str(value or ""))
        if item.strip()
    ]


def unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result


class Command(BaseCommand):
    help = "CSV fayldan Qabul 2026 matematika javob kalitini import qiladi"

    def add_arguments(self, parser):
        parser.add_argument("csv_path")
        parser.add_argument(
            "--strict",
            action="store_true",
            help="CSVdagi bo‘sh correct_answer qatorlarini xato deb hisoblash",
        )
        parser.add_argument(
            "--grade-pending",
            action="store_true",
            help="Importdan keyin pending_review urinishlarni avtomatik qayta baholash",
        )

    def handle(self, *args, **options):
        path = Path(options["csv_path"]).expanduser().resolve()
        if not path.exists():
            raise CommandError(f"CSV fayl topilmadi: {path}")

        with path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))

        if not rows:
            raise CommandError("CSV bo‘sh.")
        if "code" not in rows[0] or "correct_answer" not in rows[0]:
            raise CommandError(
                "CSVda code va correct_answer ustunlari bo‘lishi shart."
            )

        updated = 0
        blank = []
        unknown = []
        seen_codes = set()

        with transaction.atomic():
            for row_number, row in enumerate(rows, start=2):
                code = str(row.get("code") or "").strip()
                correct = str(row.get("correct_answer") or "").strip()

                if not code:
                    raise CommandError(f"{row_number}-qatorda code bo‘sh.")
                if code in seen_codes:
                    raise CommandError(f"CSVda takroriy code bor: {code}")
                seen_codes.add(code)

                if not correct:
                    blank.append(code)
                    continue

                try:
                    question = Question.objects.select_for_update().get(
                        code=code,
                        subject__slug="math",
                    )
                except Question.DoesNotExist:
                    unknown.append(code)
                    continue

                alternatives = split_alternatives(
                    row.get("alternative_answers", "")
                )
                answers = unique([correct, *alternatives])

                raw_tolerance = str(row.get("tolerance") or "0").strip()
                try:
                    tolerance = Decimal(raw_tolerance.replace(",", "."))
                except InvalidOperation as exc:
                    raise CommandError(
                        f"{code}: tolerance noto‘g‘ri — {raw_tolerance}"
                    ) from exc
                if tolerance < 0:
                    raise CommandError(
                        f"{code}: tolerance manfiy bo‘la olmaydi."
                    )

                question.accepted_text_answers = "\n".join(answers)
                question.answer_tolerance = tolerance
                question.save(
                    update_fields=[
                        "accepted_text_answers",
                        "answer_tolerance",
                        "updated_at",
                    ]
                )
                updated += 1

            if unknown:
                raise CommandError(
                    "Database’da topilmagan kodlar: "
                    + ", ".join(unknown[:20])
                )
            if options["strict"] and blank:
                raise CommandError(
                    "correct_answer bo‘sh qolgan kodlar: "
                    + ", ".join(blank[:20])
                )

        configured = Question.objects.filter(
            code__startswith="Q26-MATH-",
            subject__slug="math",
        ).exclude(accepted_text_answers="").count()
        total = Question.objects.filter(
            code__startswith="Q26-MATH-",
            subject__slug="math",
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"{updated} ta kalit yangilandi. "
                f"Umumiy holat: {configured}/{total}."
            )
        )
        if blank:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(blank)} ta bo‘sh qator tashlab ketildi."
                )
            )

        if options["grade_pending"]:
            call_command("auto_grade_pending_math")
