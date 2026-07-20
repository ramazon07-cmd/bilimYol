from django.contrib import admin

from .models import Certificate, University, UniversityGoal


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "target_math", "target_english", "target_iq", "target_ielts", "target_sat")
    search_fields = ("name", "country", "city")


@admin.register(UniversityGoal)
class UniversityGoalAdmin(admin.ModelAdmin):
    list_display = ("student", "university", "target_year", "selected_by", "updated_at")
    list_select_related = ("student", "university", "selected_by")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("student", "kind", "score", "is_verified", "issued_at")
    list_filter = ("kind", "is_verified")
