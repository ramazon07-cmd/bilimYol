import csv
import io
import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html

from .forms import MathAnswerKeyCsvUploadForm
from .models import (
    Exam,
    ExamQuestion,
    ExamSubjectWeight,
    Question,
    QuestionOption,
    Skill,
    Subject,
    Topic,
)


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

    change_list_template = "admin/academics/question/change_list.html"
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

    def get_urls(self):
        default_urls = super().get_urls()

        custom_urls = [
            path(
                "math-answer-keys/export/",
                self.admin_site.admin_view(
                    self.export_math_answer_keys
                ),
                name="academics_question_export_math_answers",
            ),
            path(
                "math-answer-keys/import/",
                self.admin_site.admin_view(
                    self.import_math_answer_keys
                ),
                name="academics_question_import_math_answers",
            ),
        ]

        return custom_urls + default_urls

    def export_math_answer_keys(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

        questions = (
            Question.objects.filter(
                code__startswith="Q26-MATH-",
                subject__slug="math",
            )
            .select_related("subject", "topic")
            .order_by("min_grade", "max_grade", "code")
        )

        response = HttpResponse(
            content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = (
            'attachment; filename="math_answer_key_final.csv"'
        )

        # Excel o‘zbekcha va boshqa belgilarni to‘g‘ri ochishi uchun.
        response.write("\ufeff")

        writer = csv.DictWriter(
            response,
            fieldnames=[
                "code",
                "grades",
                "question_number",
                "prompt",
                "image_url",
                "correct_answer",
                "alternative_answers",
                "tolerance",
            ],
        )
        writer.writeheader()

        exported_count = 0

        for question in questions:
            accepted_answers = [
                answer.strip()
                for answer in (
                    question.accepted_text_answers or ""
                ).splitlines()
                if answer.strip()
            ]

            grades = (
                str(question.min_grade)
                if question.min_grade == question.max_grade
                else f"{question.min_grade}-{question.max_grade}"
            )

            question_number = question.code.rsplit("-", 1)[-1]

            writer.writerow(
                {
                    "code": question.code,
                    "grades": grades,
                    "question_number": question_number,
                    "prompt": question.prompt,
                    "image_url": question.image_url,
                    "correct_answer": (
                        accepted_answers[0]
                        if accepted_answers
                        else ""
                    ),
                    "alternative_answers": "||".join(
                        accepted_answers[1:]
                    ),
                    "tolerance": str(
                        question.answer_tolerance or 0
                    ),
                }
            )

            if accepted_answers:
                exported_count += 1

        self.message_user(
            request,
            (
                f"CSV yaratildi. "
                f"{exported_count} ta savolda javob kaliti bor."
            ),
            level=messages.SUCCESS,
        )

        return response

    def import_math_answer_keys(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied

        if request.method == "POST":
            form = MathAnswerKeyCsvUploadForm(
                request.POST,
                request.FILES,
            )

            if form.is_valid():
                uploaded_file = form.cleaned_data["csv_file"]

                try:
                    decoded_file = uploaded_file.read().decode(
                        "utf-8-sig"
                    )
                except UnicodeDecodeError:
                    messages.error(
                        request,
                        (
                            "CSV fayl UTF-8 formatida emas. "
                            "Faylni UTF-8 CSV qilib saqlang."
                        ),
                    )
                else:
                    reader = csv.DictReader(
                        io.StringIO(decoded_file)
                    )

                    required_columns = {
                        "code",
                        "correct_answer",
                    }

                    available_columns = set(
                        reader.fieldnames or []
                    )

                    if not required_columns.issubset(
                        available_columns
                    ):
                        messages.error(
                            request,
                            (
                                "CSV faylda code va "
                                "correct_answer ustunlari "
                                "bo‘lishi shart."
                            ),
                        )
                    else:
                        updated_count = 0
                        blank_count = 0
                        unknown_codes = []

                        try:
                            with transaction.atomic():
                                for row_number, row in enumerate(
                                    reader,
                                    start=2,
                                ):
                                    code = str(
                                        row.get("code") or ""
                                    ).strip()

                                    correct_answer = str(
                                        row.get(
                                            "correct_answer"
                                        )
                                        or ""
                                    ).strip()

                                    if not code or not correct_answer:
                                        blank_count += 1
                                        continue

                                    question = (
                                        Question.objects
                                        .select_for_update()
                                        .filter(
                                            code=code,
                                            subject__slug="math",
                                        )
                                        .first()
                                    )

                                    if question is None:
                                        unknown_codes.append(code)
                                        continue

                                    alternative_value = str(
                                        row.get(
                                            "alternative_answers"
                                        )
                                        or ""
                                    )

                                    alternatives = [
                                        answer.strip()
                                        for answer in re.split(
                                            r"\|\||\r?\n",
                                            alternative_value,
                                        )
                                        if answer.strip()
                                    ]

                                    all_answers = [
                                        correct_answer,
                                        *alternatives,
                                    ]

                                    unique_answers = []
                                    seen_answers = set()

                                    for answer in all_answers:
                                        normalized = (
                                            answer.strip().casefold()
                                        )

                                        if (
                                            normalized
                                            and normalized
                                            not in seen_answers
                                        ):
                                            seen_answers.add(
                                                normalized
                                            )
                                            unique_answers.append(
                                                answer.strip()
                                            )

                                    raw_tolerance = str(
                                        row.get("tolerance") or "0"
                                    ).strip()

                                    try:
                                        tolerance = Decimal(
                                            raw_tolerance.replace(
                                                ",",
                                                ".",
                                            )
                                        )
                                    except InvalidOperation as exc:
                                        raise ValueError(
                                            (
                                                f"{row_number}-qator, "
                                                f"{code}: tolerance "
                                                f"noto‘g‘ri — "
                                                f"{raw_tolerance}"
                                            )
                                        ) from exc

                                    if tolerance < 0:
                                        raise ValueError(
                                            (
                                                f"{row_number}-qator, "
                                                f"{code}: tolerance "
                                                "manfiy bo‘la olmaydi."
                                            )
                                        )

                                    question.accepted_text_answers = (
                                        "\n".join(unique_answers)
                                    )
                                    question.answer_tolerance = (
                                        tolerance
                                    )
                                    question.save(
                                        update_fields=[
                                            "accepted_text_answers",
                                            "answer_tolerance",
                                            "updated_at",
                                        ]
                                    )

                                    updated_count += 1

                        except ValueError as exc:
                            messages.error(
                                request,
                                str(exc),
                            )
                        else:
                            messages.success(
                                request,
                                (
                                    f"{updated_count} ta savolning "
                                    "javobi muvaffaqiyatli yuklandi."
                                ),
                            )

                            if blank_count:
                                messages.warning(
                                    request,
                                    (
                                        f"{blank_count} ta bo‘sh "
                                        "qator tashlab ketildi."
                                    ),
                                )

                            if unknown_codes:
                                shown_codes = ", ".join(
                                    unknown_codes[:10]
                                )

                                messages.warning(
                                    request,
                                    (
                                        f"{len(unknown_codes)} ta kod "
                                        "database’da topilmadi: "
                                        f"{shown_codes}"
                                    ),
                                )

                            return redirect(
                                "admin:academics_question_changelist"
                            )
        else:
            form = MathAnswerKeyCsvUploadForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Matematika javoblarini CSV orqali yuklash",
            "opts": self.model._meta,
            "form": form,
        }

        return TemplateResponse(
            request,
            (
                "admin/academics/question/"
                "math_answer_key_import.html"
            ),
            context,
        )


admin.site.register(Subject)
admin.site.register(Topic)
admin.site.register(Skill)
admin.site.register(Exam)
admin.site.register(ExamSubjectWeight)
admin.site.register(ExamQuestion)
