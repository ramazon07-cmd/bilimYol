import csv
from pathlib import Path
import re

from django.core.management.base import BaseCommand

from apps.academics.models import Question


SOURCE_ORDER = {
    "G2": 1,
    "G3": 2,
    "G4": 3,
    "G5": 4,
    "G6": 5,
    "G7": 6,
    "G8-9": 7,
    "G10-11": 8,
}


def source_key(code: str) -> str:
    match = re.match(r"^Q26-MATH-(.+)-(\d{2})$", code)
    return match.group(1) if match else ""


def question_number(code: str) -> int:
    match = re.search(r"-(\d{2})$", code)
    return int(match.group(1)) if match else 0


class Command(BaseCommand):
    help = "Qabul 2026 matematika javob kaliti CSV shablonini chiqaradi"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="math_answer_key.csv",
            help="CSV chiqish manzili",
        )
        parser.add_argument(
            "--grade",
            type=int,
            choices=range(2, 12),
            help="Faqat shu sinf savollarini chiqarish",
        )

    def handle(self, *args, **options):
        questions = list(
            Question.objects.filter(
                code__startswith="Q26-MATH-",
                subject__slug="math",
            )
        )
        if options["grade"]:
            grade = options["grade"]
            questions = [
                item
                for item in questions
                if item.min_grade <= grade <= item.max_grade
            ]

        questions.sort(
            key=lambda item: (
                SOURCE_ORDER.get(source_key(item.code), 99),
                question_number(item.code),
            )
        )

        output = Path(options["output"]).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "code",
                    "grades",
                    "question_number",
                    "prompt",
                    "image_url",
                    "correct_answer",
                    "alternative_answers",
                    "tolerance",
                ],
            )
            writer.writeheader()
            for question in questions:
                current = [
                    row.strip()
                    for row in question.accepted_text_answers.splitlines()
                    if row.strip()
                ]
                grades = (
                    str(question.min_grade)
                    if question.min_grade == question.max_grade
                    else f"{question.min_grade}-{question.max_grade}"
                )
                writer.writerow({
                    "code": question.code,
                    "grades": grades,
                    "question_number": question_number(question.code),
                    "prompt": question.prompt,
                    "image_url": question.image_url,
                    "correct_answer": current[0] if current else "",
                    "alternative_answers": "||".join(current[1:]),
                    "tolerance": str(question.answer_tolerance or 0),
                })

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(questions)} ta savol shabloni yaratildi: {output}"
            )
        )
