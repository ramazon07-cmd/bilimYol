from django.contrib import admin

from .models import Category, GuardianContact, InterviewAnswer, StudentCategory, StudentGoal, StudentInterview, StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ["admission_code", "student", "grade", "status", "assigned_admin", "assigned_teacher"]
    list_filter = ["status", "grade", "region"]
    search_fields = ["admission_code", "student__full_name", "student__username", "student__phone"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "subject_slug", "is_active"]
    list_filter = ["kind", "subject_slug", "is_active"]


admin.site.register(GuardianContact)
admin.site.register(StudentCategory)
admin.site.register(StudentGoal)
admin.site.register(StudentInterview)
admin.site.register(InterviewAnswer)
