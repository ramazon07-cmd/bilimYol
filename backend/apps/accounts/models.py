from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "O‘quvchi"
        TEACHER = "teacher", "O‘qituvchi"
        PARENT = "parent", "Ota-ona"
        ADMIN = "admin", "Administrator"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT, db_index=True)
    full_name = models.CharField(max_length=180)
    phone = models.CharField(max_length=30, blank=True)
    avatar_url = models.URLField(blank=True)

    def __str__(self) -> str:
        return self.full_name or self.username


class Classroom(models.Model):
    name = models.CharField(max_length=80)
    grade = models.PositiveSmallIntegerField(default=8)
    program = models.CharField(max_length=160, default="Prezident maktabiga tayyorgarlik")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="teaching_classes", limit_choices_to={"role": User.Role.TEACHER})
    students = models.ManyToManyField(User, through="ClassroomStudent", related_name="classrooms")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["grade", "name"]

    def __str__(self) -> str:
        return f"{self.name} · {self.program}"


class ClassroomStudent(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="class_enrollments", limit_choices_to={"role": User.Role.STUDENT})
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["classroom", "student"], name="unique_classroom_student")]


class ParentStudent(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="children_links", limit_choices_to={"role": User.Role.PARENT})
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parent_links", limit_choices_to={"role": User.Role.STUDENT})
    relationship = models.CharField(max_length=40, default="Ota-ona")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["parent", "student"], name="unique_parent_student")]

    def __str__(self) -> str:
        return f"{self.parent} → {self.student}"
