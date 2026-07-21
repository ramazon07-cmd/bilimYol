from django.db.models import Q

from apps.academics.models import Exam

from .models import StudentProfile


def recommend_exams(profile: StudentProfile):
    category_ids = profile.category_links.filter(is_active=True).values_list("category_id", flat=True)
    queryset = Exam.objects.filter(status__in=[Exam.Status.ACTIVE, Exam.Status.SCHEDULED])
    if profile.grade:
        queryset = queryset.filter(Q(grade=profile.grade) | Q(grade__isnull=True))
    if category_ids:
        queryset = queryset.filter(
            Q(recommended_categories__in=category_ids) | Q(recommended_categories__isnull=True)
        )
    return queryset.distinct()
