from django.conf import settings
from django.db.models import Exists, OuterRef

from .models import ExamQuestion


def active_diagnostic_subject_slugs() -> tuple[str, ...]:
    configured = getattr(settings, "DIAGNOSTIC_ACTIVE_SUBJECTS", ("english",))
    return tuple(str(item).strip().lower() for item in configured if str(item).strip())


def enabled_diagnostic_exams(queryset):
    question_rows = ExamQuestion.objects.filter(exam_id=OuterRef("pk"))
    disabled_question_rows = question_rows.exclude(
        question__subject__slug__in=active_diagnostic_subject_slugs(),
    )
    return queryset.annotate(
        _has_diagnostic_questions=Exists(question_rows),
        _has_disabled_subject_questions=Exists(disabled_question_rows),
    ).filter(
        _has_diagnostic_questions=True,
        _has_disabled_subject_questions=False,
    )


def is_enabled_diagnostic_exam(exam) -> bool:
    return enabled_diagnostic_exams(exam.__class__.objects.filter(pk=exam.pk)).exists()
