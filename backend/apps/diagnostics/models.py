from django.conf import settings
from django.db import models

from apps.accounts.models import Classroom
from apps.academics.models import Exam, ExamQuestion, QuestionOption, Skill, Subject, Topic


class ExamAssignment(models.Model):
    class DeliveryMode(models.TextChoices):
        SELF = "self", "O‘quvchi mustaqil"
        ADMINISTERED = "administered", "Admin bilan"

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="assignments")
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.SET_NULL,
        related_name="exam_assignments",
        null=True,
        blank=True,
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_assignments",
        limit_choices_to={"role": "student"},
    )
    available_from = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_exams",
    )
    delivery_mode = models.CharField(
        max_length=20,
        choices=DeliveryMode.choices,
        default=DeliveryMode.SELF,
    )
    administered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="administered_exam_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["exam", "student"], name="unique_exam_student_assignment")
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.exam} → {self.student}"


class ExamAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "Jarayonda"
        SUBMITTED = "submitted", "Topshirildi"
        EXPIRED = "expired", "Vaqt tugadi"

    assignment = models.ForeignKey(ExamAssignment, on_delete=models.CASCADE, related_name="attempts")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="started_exam_attempts",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_exam_attempts",
    )
    earned_points = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overall_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_ready = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.assignment.student} · {self.assignment.exam}"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name="answers")
    exam_question = models.ForeignKey(ExamQuestion, on_delete=models.PROTECT, related_name="student_answers")
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.PROTECT, related_name="student_selections")
    is_correct = models.BooleanField(default=False)
    earned_points = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_flagged = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["attempt", "exam_question"], name="unique_attempt_question_answer")
        ]


class DiagnosticReport(models.Model):
    class Readiness(models.TextChoices):
        READY = "ready", "Tayyor"
        NOT_READY = "not_ready", "Tayyor emas"

    attempt = models.OneToOneField(ExamAttempt, on_delete=models.CASCADE, related_name="report")
    overall_score = models.DecimalField(max_digits=6, decimal_places=2)
    range_low = models.DecimalField(max_digits=6, decimal_places=2)
    range_high = models.DecimalField(max_digits=6, decimal_places=2)
    expected_score = models.DecimalField(max_digits=6, decimal_places=2)
    readiness = models.CharField(max_length=16, choices=Readiness.choices)
    summary = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-generated_at"]


class SubjectResult(models.Model):
    report = models.ForeignKey(DiagnosticReport, on_delete=models.CASCADE, related_name="subject_results")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="diagnostic_results")
    earned_points = models.DecimalField(max_digits=8, decimal_places=2)
    possible_points = models.DecimalField(max_digits=8, decimal_places=2)
    score = models.DecimalField(max_digits=6, decimal_places=2)
    weight_percent = models.DecimalField(max_digits=5, decimal_places=2)
    level = models.CharField(max_length=30)
    percentile = models.PositiveSmallIntegerField(default=0)
    rank = models.CharField(max_length=40, blank=True)
    potential = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["report", "subject"], name="unique_report_subject_result")
        ]


class TopicResult(models.Model):
    report = models.ForeignKey(DiagnosticReport, on_delete=models.CASCADE, related_name="topic_results")
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name="diagnostic_results")
    earned_points = models.DecimalField(max_digits=8, decimal_places=2)
    possible_points = models.DecimalField(max_digits=8, decimal_places=2)
    score = models.DecimalField(max_digits=6, decimal_places=2)
    question_count = models.PositiveSmallIntegerField(default=0)
    confidence = models.CharField(max_length=20, default="low")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["report", "topic"], name="unique_report_topic_result")
        ]


class SkillResult(models.Model):
    report = models.ForeignKey(DiagnosticReport, on_delete=models.CASCADE, related_name="skill_results")
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="diagnostic_results")
    earned_points = models.DecimalField(max_digits=8, decimal_places=2)
    possible_points = models.DecimalField(max_digits=8, decimal_places=2)
    score = models.DecimalField(max_digits=6, decimal_places=2)
    question_count = models.PositiveSmallIntegerField(default=0)
    confidence = models.CharField(max_length=20, default="low")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["report", "skill"], name="unique_report_skill_result")
        ]


class Roadmap(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Tasdiqlangan"
        ACTIVE = "active", "Faol"
        COMPLETED = "completed", "Yakunlangan"

    report = models.OneToOneField(DiagnosticReport, on_delete=models.CASCADE, related_name="roadmap")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roadmaps",
        limit_choices_to={"role": "student"},
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_roadmaps",
        limit_choices_to={"role": "teacher"},
    )
    primary_goal = models.ForeignKey(
        "profiling.StudentGoal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roadmaps",
    )
    generation_context = models.JSONField(default=dict, blank=True)
    admin_note = models.TextField(blank=True)
    target_score = models.PositiveSmallIntegerField(default=85)
    weekly_hours = models.PositiveSmallIntegerField(default=5)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class RoadmapStage(models.Model):
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name="stages")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="roadmap_stages")
    focus_topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name="roadmap_stages")
    order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=180)
    start_month = models.PositiveSmallIntegerField(default=0)
    end_month = models.PositiveSmallIntegerField(default=3)
    start_score = models.PositiveSmallIntegerField(default=0)
    target_score = models.PositiveSmallIntegerField(default=60)
    weekly_hours = models.PositiveSmallIntegerField(default=4)
    rationale = models.TextField(blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["roadmap", "order"], name="unique_roadmap_stage_order")
        ]


class WeeklyTask(models.Model):
    class Audience(models.TextChoices):
        STUDENT = "student", "O‘quvchi"
        TEACHER = "teacher", "O‘qituvchi"
        PARENT = "parent", "Ota-ona"

    stage = models.ForeignKey(RoadmapStage, on_delete=models.CASCADE, related_name="weekly_tasks")
    week_number = models.PositiveSmallIntegerField()
    audience = models.CharField(max_length=16, choices=Audience.choices, default=Audience.STUDENT)
    title = models.CharField(max_length=180)
    description = models.TextField()
    resource_url = models.URLField(blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["week_number", "audience", "id"]
