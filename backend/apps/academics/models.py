from django.conf import settings
from django.db import models


class Subject(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=120)
    color = models.CharField(max_length=20, default="#65001F")
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self) -> str:
        return self.title


class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    code = models.CharField(max_length=40, blank=True)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    healthy_threshold = models.PositiveSmallIntegerField(default=75)
    prerequisites = models.ManyToManyField("self", symmetrical=False, blank=True, related_name="unlocks")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["subject", "order", "title"]
        constraints = [models.UniqueConstraint(fields=["subject", "code"], name="unique_subject_topic_code")]

    def __str__(self) -> str:
        return f"{self.subject}: {self.title}"


class Skill(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="skills")
    slug = models.SlugField()
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["subject", "order", "title"]
        constraints = [models.UniqueConstraint(fields=["subject", "slug"], name="unique_subject_skill_slug")]

    def __str__(self) -> str:
        return f"{self.subject}: {self.title}"


class Question(models.Model):
    class Difficulty(models.TextChoices):
        BASIC = "basic", "Boshlang‘ich"
        MEDIUM = "medium", "O‘rta"
        HIGH = "high", "Yuqori"

    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="questions")
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name="questions")
    skills = models.ManyToManyField(Skill, related_name="questions")
    code = models.CharField(max_length=40, unique=True)
    context = models.TextField(
        blank=True,
        help_text="Reading passage, scenario yoki savolga tegishli umumiy matn.",
    )
    prompt = models.TextField()
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(max_length=12, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    min_grade = models.PositiveSmallIntegerField(null=True, blank=True)
    max_grade = models.PositiveSmallIntegerField(null=True, blank=True)
    default_points = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_questions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["subject", "code"]

    def __str__(self) -> str:
        return f"{self.code}: {self.prompt[:60]}"


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=4)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [models.UniqueConstraint(fields=["question", "label"], name="unique_question_option_label")]

    def __str__(self) -> str:
        return f"{self.question.code}-{self.label}"


class Exam(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Rejalashtirilgan"
        ACTIVE = "active", "Faol"
        COMPLETED = "completed", "Yakunlangan"
        ARCHIVED = "archived", "Arxivlangan"

    class Purpose(models.TextChoices):
        ADMISSION = "admission", "Qabul diagnostikasi"
        PRESIDENTIAL_SCHOOL = "presidential_school", "Prezident maktabi"
        IELTS = "ielts", "IELTS"
        SAT = "sat", "SAT"
        OLYMPIAD = "olympiad", "Olimpiada"
        GENERAL = "general", "Umumiy diagnostika"

    title = models.CharField(max_length=180)
    grade = models.PositiveSmallIntegerField(null=True, blank=True)
    purpose = models.CharField(max_length=40, choices=Purpose.choices, default=Purpose.GENERAL, db_index=True)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=90)
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=100)
    readiness_threshold = models.PositiveSmallIntegerField(default=67)
    minimum_subject_score = models.PositiveSmallIntegerField(default=50)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    subjects = models.ManyToManyField(Subject, through="ExamSubjectWeight", related_name="exams")
    recommended_categories = models.ManyToManyField(
        "profiling.Category",
        related_name="recommended_exams",
        blank=True,
    )
    target_classrooms = models.ManyToManyField(
        "accounts.Classroom",
        related_name="available_exams",
        blank=True,
        help_text="Test qaysi sinflar uchun tayyorlanganini belgilaydi.",
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_exams")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-starts_at", "-created_at"]

    def __str__(self) -> str:
        return self.title


class ExamSubjectWeight(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="subject_weights")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="exam_weights")
    weight_percent = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=100)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["exam", "subject"], name="unique_exam_subject_weight")]


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="exam_questions")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="exam_uses")
    points = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [models.UniqueConstraint(fields=["exam", "question"], name="unique_exam_question")]

    def __str__(self) -> str:
        return f"{self.exam}: {self.question.code}"
