from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import Classroom, ClassroomStudent

from .models import StudentProfile


User = get_user_model()


def classroom_for_grade(grade: int, teacher=None) -> Classroom:
    expected_name = f"{grade}-A"
    classroom = (
        Classroom.objects.filter(name=expected_name, is_active=True).order_by("id").first()
        or Classroom.objects.filter(grade=grade, is_active=True).order_by("name", "id").first()
    )

    if classroom is None:
        classroom = Classroom.objects.create(
            name=expected_name,
            grade=grade,
            program="Prezident maktabiga tayyorgarlik",
            teacher=teacher,
            is_active=True,
        )
        return classroom

    changed_fields = []
    if classroom.grade != grade:
        classroom.grade = grade
        changed_fields.append("grade")
    if teacher and classroom.teacher_id is None:
        classroom.teacher = teacher
        changed_fields.append("teacher")
    if not classroom.is_active:
        classroom.is_active = True
        changed_fields.append("is_active")
    if changed_fields:
        classroom.save(update_fields=changed_fields)
    return classroom


@receiver(post_save, sender=StudentProfile)
def enroll_profile_in_grade_classroom(sender, instance: StudentProfile, raw=False, **kwargs):
    if raw or not instance.grade or instance.student.role != User.Role.STUDENT:
        return

    teacher = instance.assigned_teacher or User.objects.filter(role=User.Role.TEACHER).order_by("id").first()
    classroom = classroom_for_grade(instance.grade, teacher=teacher)

    ClassroomStudent.objects.filter(student=instance.student).exclude(
        classroom__grade=instance.grade,
    ).delete()
    ClassroomStudent.objects.get_or_create(
        classroom=classroom,
        student=instance.student,
    )
