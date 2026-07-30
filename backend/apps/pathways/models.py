from django.conf import settings
from django.db import models


class University(models.Model):
    name = models.CharField(max_length=180, unique=True)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    logo_url = models.URLField(blank=True)
    target_math = models.PositiveSmallIntegerField(default=80)
    target_english = models.PositiveSmallIntegerField(default=80)
    target_iq = models.PositiveSmallIntegerField(default=80)
    target_ielts = models.DecimalField(max_digits=3, decimal_places=1, default=6.5)
    target_sat = models.PositiveSmallIntegerField(default=1400)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} · {self.country}"


class UniversityGoal(models.Model):
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="university_goal",
        limit_choices_to={"role": "student"},
    )
    university = models.ForeignKey(University, on_delete=models.PROTECT, related_name="student_goals")
    target_year = models.PositiveSmallIntegerField()
    selected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="selected_university_goals")
    selected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.student} → {self.university}"


class Certificate(models.Model):
    class Kind(models.TextChoices):
        IELTS = "ielts", "IELTS"
        SAT = "sat", "SAT"
        CEFR = "cefr", "CEFR"
        OTHER = "other", "Boshqa"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Tekshiruvda"
        VERIFIED = "verified", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates", limit_choices_to={"role": "student"})
    kind = models.CharField(max_length=16, choices=Kind.choices)
    title = models.CharField(max_length=180)
    score = models.DecimalField(max_digits=7, decimal_places=2)
    issued_at = models.DateField()
    expires_at = models.DateField(null=True, blank=True)
    file_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    verification_status = models.CharField(
        max_length=16,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    verification_note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_certificates")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at", "-created_at"]

    def __str__(self) -> str:
        return f"{self.student} · {self.get_kind_display()} {self.score}"
