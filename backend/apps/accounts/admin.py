from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Classroom, ClassroomStudent, ParentStudent, User


@admin.register(User)
class BilimUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("BilimYo‘l", {"fields": ("full_name", "role", "phone", "avatar_url")}),)
    list_display = ["username", "full_name", "role", "email", "is_active"]
    list_filter = ["role", "is_active"]


admin.site.register(Classroom)
admin.site.register(ClassroomStudent)
admin.site.register(ParentStudent)
