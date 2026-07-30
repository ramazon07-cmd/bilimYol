from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.crypto import get_random_string


def generate_admission_code() -> str:
    return f"BY-{get_random_string(6, allowed_chars='0123456789')}"


class StudentProfile(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        INTERVIEW_DRAFT = "interview_draft", "Suhbat jarayonida"
        INTERVIEW_COMPLETED = "interview_completed", "Suhbat yakunlandi"
        TEST_RECOMMENDED = "test_recommended", "Test tavsiya qilindi"
        TEST_ASSIGNED = "test_assigned", "Test biriktirildi"
        DIAGNOSED = "diagnosed", "Diagnostika yakunlandi"
        ROADMAP_DRAFT = "roadmap_draft", "Roadmap tayyorlanmoqda"
        ACTIVE = "active", "Faol o‘quvchi"
        PAUSED = "paused", "Vaqtincha to‘xtatilgan"

    class LearningStyle(models.TextChoices):
        VISUAL = "visual", "Vizual"
        PRACTICAL = "practical", "Amaliy"
        READING = "reading", "O‘qish orqali"
        MIXED = "mixed", "Aralash"
        UNKNOWN = "unknown", "Aniqlanmagan"

    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": "student"},
    )
    admission_code = models.CharField(max_length=20, unique=True, default=generate_admission_code)
    birth_date = models.DateField(null=True, blank=True)
    school_name = models.CharField(max_length=200, blank=True)
    grade = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(11)],
    )
    region = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    weekly_study_hours = models.PositiveSmallIntegerField(default=5)
    learning_style = models.CharField(
        max_length=20,
        choices=LearningStyle.choices,
        default=LearningStyle.UNKNOWN,
    )
    internet_access = models.BooleanField(default=True)
    device_access = models.BooleanField(default=True)
    assigned_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_student_profiles",
        limit_choices_to={"role": "admin"},
    )
    assigned_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_student_profiles",
        limit_choices_to={"role": "teacher"},
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.admission_code} · {self.student.full_name}"


class GuardianContact(models.Model):
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="guardian_contacts")
    full_name = models.CharField(max_length=180)
    relationship = models.CharField(max_length=50, default="Ota-ona")
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    workplace = models.CharField(max_length=180, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.full_name} · {self.profile.student.full_name}"


class Category(models.Model):
    class Kind(models.TextChoices):
        DIRECTION = "direction", "Ta’lim yo‘nalishi"
        SUBJECT_LEVEL = "subject_level", "Fan darajasi"
        SUPPORT = "support", "Qo‘llab-quvvatlash"
        MOTIVATION = "motivation", "Motivatsiya"
        LEARNING_STYLE = "learning_style", "O‘rganish usuli"
        SPECIAL = "special", "Maxsus holat"

    code = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=30, choices=Kind.choices, db_index=True)
    subject_slug = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, default="#65001F")
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["kind", "order", "title"]

    def __str__(self) -> str:
        return self.title


class StudentCategory(models.Model):
    class Source(models.TextChoices):
        MANUAL = "manual", "Admin tomonidan"
        INTERVIEW = "interview", "Suhbat natijasida"
        DIAGNOSTIC = "diagnostic", "Diagnostika natijasida"

    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="category_links")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="student_links")
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    confidence = models.PositiveSmallIntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    note = models.TextField(blank=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile", "category"], name="unique_student_profile_category")
        ]


class StudentGoal(models.Model):
    class GoalType(models.TextChoices):
        PRESIDENTIAL_SCHOOL = "presidential_school", "Prezident maktabi"
        IELTS = "ielts", "IELTS"
        SAT = "sat", "SAT"
        UNIVERSITY = "university", "Universitet"
        OLYMPIAD = "olympiad", "Olimpiada"
        SCHOOL_IMPROVEMENT = "school_improvement", "Maktab natijasi"
        GENERAL = "general", "Umumiy rivojlanish"
        OTHER = "other", "Boshqa"

    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="goals")
    goal_type = models.CharField(max_length=40, choices=GoalType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    current_value = models.CharField(max_length=100, blank=True)
    target_value = models.CharField(max_length=100, blank=True)
    target_score = models.PositiveSmallIntegerField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(default=1)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["priority", "-is_primary", "created_at"]


class StudentInterview(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Jarayonda"
        COMPLETED = "completed", "Yakunlangan"

    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="interviews")
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conducted_student_interviews",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    main_problem = models.TextField(blank=True)
    motivation_level = models.CharField(max_length=30, blank=True)
    independence_level = models.CharField(max_length=30, blank=True)
    parent_support_level = models.CharField(max_length=30, blank=True)
    admin_summary = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    next_step = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]


class InterviewAnswer(models.Model):
    interview = models.ForeignKey(StudentInterview, on_delete=models.CASCADE, related_name="answers")
    question_key = models.CharField(max_length=100)
    question_text = models.CharField(max_length=300)
    answer_text = models.TextField(blank=True)
    score = models.SmallIntegerField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["interview", "question_key"], name="unique_interview_question")
        ]
