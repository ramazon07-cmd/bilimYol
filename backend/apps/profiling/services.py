from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q

from apps.academics.models import Exam
from apps.academics.policies import enabled_diagnostic_exams

from .models import StudentProfile

def recommend_exams(profile: StudentProfile):
    """Return every enabled active diagnostic for the student's exact grade.

    Categories never hide another exact-grade subject. A grade 3 student sees
    both grade 3 English and Mathematics when both tests are active.
    """
    # bilimyol-all-grade-tests-hotfix-v4
    queryset = enabled_diagnostic_exams(
        Exam.objects.filter(
            status__in=[Exam.Status.ACTIVE, Exam.Status.SCHEDULED],
        )
    )

    if profile.grade:
        exact_grade = queryset.filter(grade=profile.grade).distinct().order_by("title")
        if exact_grade.exists():
            return exact_grade

    return queryset.filter(grade__isnull=True).distinct().order_by("title")
