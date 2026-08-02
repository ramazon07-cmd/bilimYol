from django.contrib import admin, messages

from .models import (
    DiagnosticReport,
    ExamAssignment,
    ExamAttempt,
    Roadmap,
    RoadmapStage,
    SkillResult,
    StudentAnswer,
    SubjectResult,
    TopicResult,
    WeeklyTask,
)
from .services import finalize_manual_attempt


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id", "student_name", "exam_title", "question_code", "text_answer",
        "manual_score", "is_graded", "earned_points",
    )
    list_filter = ("is_graded", "attempt__status", "attempt__assignment__exam")
    search_fields = (
        "attempt__assignment__student__full_name",
        "attempt__assignment__student__username",
        "exam_question__question__code",
        "text_answer",
    )
    list_editable = ("manual_score", "is_graded")
    list_select_related = (
        "attempt__assignment__student",
        "attempt__assignment__exam",
        "exam_question__question",
    )

    @admin.display(description="O‘quvchi")
    def student_name(self, obj):
        return obj.attempt.assignment.student.full_name

    @admin.display(description="Test")
    def exam_title(self, obj):
        return obj.attempt.assignment.exam.title

    @admin.display(description="Savol")
    def question_code(self, obj):
        return obj.exam_question.question.code


@admin.action(description="Tanlangan yozma urinishlarni yakuniy baholash")
def finalize_selected_attempts(modeladmin, request, queryset):
    completed = 0
    for attempt in queryset:
        try:
            finalize_manual_attempt(attempt, graded_by=request.user)
            completed += 1
        except Exception as exc:
            modeladmin.message_user(
                request, f"{attempt}: {exc}", level=messages.ERROR
            )
    if completed:
        modeladmin.message_user(
            request, f"{completed} ta matematika urinishi yakunlandi.",
            level=messages.SUCCESS,
        )


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "student_name", "exam_title", "status", "submitted_at", "overall_score")
    list_filter = ("status", "assignment__exam")
    actions = (finalize_selected_attempts,)

    @admin.display(description="O‘quvchi")
    def student_name(self, obj):
        return obj.assignment.student.full_name

    @admin.display(description="Test")
    def exam_title(self, obj):
        return obj.assignment.exam.title


admin.site.register(ExamAssignment)
admin.site.register(DiagnosticReport)
admin.site.register(SubjectResult)
admin.site.register(TopicResult)
admin.site.register(SkillResult)
admin.site.register(Roadmap)
admin.site.register(RoadmapStage)
admin.site.register(WeeklyTask)
