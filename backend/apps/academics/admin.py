from django.contrib import admin

from .models import Exam, ExamQuestion, ExamSubjectWeight, Question, QuestionOption, Skill, Subject, Topic


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["code", "subject", "topic", "difficulty", "is_active"]
    list_filter = ["subject", "difficulty", "is_active"]
    search_fields = ["code", "prompt", "topic__title"]
    filter_horizontal = ["skills"]
    inlines = [QuestionOptionInline]


admin.site.register(Subject)
admin.site.register(Topic)
admin.site.register(Skill)
admin.site.register(Exam)
admin.site.register(ExamSubjectWeight)
admin.site.register(ExamQuestion)
