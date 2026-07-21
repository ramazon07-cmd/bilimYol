from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q

from apps.academics.models import Exam

from .models import StudentProfile


def recommend_exams(profile: StudentProfile):
    """Return the best active tests without failing because of optional tags.

    Priority:
    1. Same grade + matching category
    2. Same grade
    3. General test with no grade
    """
    queryset = Exam.objects.filter(
        status__in=[Exam.Status.ACTIVE, Exam.Status.SCHEDULED],
    )

    if profile.grade:
        grade_pool = queryset.filter(Q(grade=profile.grade) | Q(grade__isnull=True))
    else:
        grade_pool = queryset

    try:
        Exam._meta.get_field("recommended_categories")
    except FieldDoesNotExist:
        category_supported = False
    else:
        category_supported = True

    if category_supported:
        category_ids = list(
            profile.category_links.filter(is_active=True).values_list("category_id", flat=True)
        )
        if category_ids:
            matched = grade_pool.filter(recommended_categories__in=category_ids).distinct()
            if matched.exists():
                return matched

    if profile.grade:
        exact_grade = queryset.filter(grade=profile.grade).distinct()
        if exact_grade.exists():
            return exact_grade

    return grade_pool.filter(grade__isnull=True).distinct()
