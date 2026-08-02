from django.core.management.base import BaseCommand
from django.db import transaction

from apps.diagnostics.models import ExamAttempt
from apps.diagnostics.services import submit_attempt
from apps.diagnostics.text_answer_grading import (
    grade_attempt_from_answer_key,
)


class Command(BaseCommand):
    help = (
        "Javob kaliti to‘liq bo‘lgan pending matematika "
        "urinishlarini baholaydi"
    )

    def add_arguments(self, parser):
        parser.add_argument("--attempt-id", type=int)

    def handle(self, *args, **options):
        queryset = ExamAttempt.objects.filter(
            status=ExamAttempt.Status.PENDING_REVIEW,
            assignment__exam__title__startswith=(
                "Qabul 2026 Matematika"
            ),
        ).select_related(
            "assignment__exam",
            "assignment__student",
            "submitted_by",
        )

        if options["attempt_id"]:
            queryset = queryset.filter(id=options["attempt_id"])

        completed = 0
        skipped = 0
        failed = 0

        for item in queryset.order_by("id"):
            try:
                with transaction.atomic():
                    attempt = (
                        ExamAttempt.objects.select_for_update()
                        .select_related(
                            "assignment__exam",
                            "assignment__student",
                        )
                        .get(id=item.id)
                    )
                    if not grade_attempt_from_answer_key(attempt):
                        skipped += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"SKIP #{attempt.id}: "
                                "javob kaliti to‘liq emas."
                            )
                        )
                        continue

                    original_submitter = attempt.submitted_by
                    attempt.status = ExamAttempt.Status.IN_PROGRESS
                    attempt.save(update_fields=["status"])

                    report = submit_attempt(
                        attempt,
                        submitted_by=original_submitter,
                        allow_inactive_exam=True,
                        build_roadmap_after=True,
                        mark_profile=True,
                    )
                    completed += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"OK #{attempt.id}: "
                            f"{attempt.assignment.student.full_name} — "
                            f"{report.overall_score}/100"
                        )
                    )
            except Exception as exc:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"XATO #{item.id}: {exc}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Yakunlandi: {completed}; "
                f"skip: {skipped}; xato: {failed}."
            )
        )
