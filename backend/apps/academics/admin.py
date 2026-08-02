from django.contrib import admin

from .models import Exam, ExamQuestion, ExamSubjectWeight, Question, QuestionOption, Skill, Subject, Topic
from django.conf import settings
from django.utils.html import format_html


class TextAnswerKeyFilter(admin.SimpleListFilter):
    title = "Yozma javob kaliti"
    parameter_name = "has_text_answer_key"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Javob yozilgan"),
            ("no", "Javob yozilmagan"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(accepted_text_answers="")

        if self.value() == "no":
            return queryset.filter(accepted_text_answers="")

        return queryset

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "subject",
        "topic",
        "difficulty",
        "has_text_answer_key",
        "answer_tolerance",
        "is_active",
    ]
    list_filter = [
        "subject",
        TextAnswerKeyFilter,
        "difficulty",
        "is_active",
    ]
    search_fields = ["code", "prompt", "topic__title"]
    filter_horizontal = ["skills"]
    inlines = [QuestionOptionInline]

    readonly_fields = [
        "question_image_preview",
        "image_url",
    ]

    fieldsets = (
        (
            "Savol ma’lumotlari",
            {
                "fields": (
                    "subject",
                    "topic",
                    "skills",
                    "code",
                    "context",
                    "prompt",
                    "explanation",
                    "difficulty",
                    "min_grade",
                    "max_grade",
                    "default_points",
                )
            },
        ),
        (
            "Savol rasmi",
            {
                "fields": (
                    "question_image_preview",
                    "image_url",
                )
            },
        ),
        (
            "Yozma javob kaliti",
            {
                "fields": (
                    "accepted_text_answers",
                    "answer_tolerance",
                )
            },
        ),
        (
            "Holat",
            {
                "fields": (
                    "is_active",
                    "created_by",
                )
            },
        ),
    )

    @admin.display(description="Savol rasmi")
    def question_image_preview(self, obj):
        if not obj or not obj.image_url:
            return "Bu savolda rasm mavjud emas."

        image_url = obj.image_url

        if image_url.startswith("/"):
            image_url = (
                f"{settings.FRONTEND_PUBLIC_URL}"
                f"{image_url}"
            )

        return format_html(
            """
            <div style="
                background: #ffffff;
                display: inline-block;
                padding: 16px;
                border-radius: 10px;
                border: 1px solid #cccccc;
                max-width: 100%;
            ">
                <a href="{}" target="_blank">
                    <img
                        src="{}"
                        alt="Savol rasmi"
                        style="
                            display: block;
                            max-width: 900px;
                            width: 100%;
                            height: auto;
                            object-fit: contain;
                        "
                    >
                </a>
            </div>
            """,
            image_url,
            image_url,
        )

    @admin.display(
        boolean=True,
        description="Yozma javob kaliti",
    )
    def has_text_answer_key(self, obj):
        return bool(obj.accepted_text_answers.strip())


admin.site.register(Subject)
admin.site.register(Topic)
admin.site.register(Skill)
admin.site.register(Exam)
admin.site.register(ExamSubjectWeight)
admin.site.register(ExamQuestion)
