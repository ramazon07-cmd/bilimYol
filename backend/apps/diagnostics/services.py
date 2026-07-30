from collections import defaultdict
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from random import SystemRandom

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.academics.policies import is_enabled_diagnostic_exam

from .models import (
    DiagnosticReport,
    ExamAttempt,
    Roadmap,
    RoadmapStage,
    SkillResult,
    SubjectResult,
    TopicResult,
    WeeklyTask,
)


def rounded(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def score_level(score: Decimal) -> str:
    value = float(score)
    if value < 35:
        return "Sayoz"
    if value < 50:
        return "Zaif"
    if value < 67:
        return "O‘rtacha"
    if value < 84:
        return "Yaxshi"
    return "Juda yaxshi"


def subject_level(subject_slug: str, score: Decimal) -> str:
    if subject_slug != "english":
        return score_level(score)
    value = float(score)
    if value <= 20:
        return "A1"
    if value <= 40:
        return "A2"
    if value <= 60:
        return "B1"
    if value <= 80:
        return "B2"
    return "C1"


def confidence_for(question_count: int) -> str:
    if question_count >= 5:
        return "high"
    if question_count >= 3:
        return "medium"
    return "low"


@transaction.atomic
def submit_attempt(attempt: ExamAttempt, submitted_by=None, *, allow_inactive_exam=False) -> DiagnosticReport:
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        raise ValidationError("Bu urinish allaqachon yakunlangan.")

    exam = attempt.assignment.exam
    if not allow_inactive_exam and not is_enabled_diagnostic_exam(exam):
        raise ValidationError("Hozircha faqat English diagnostik testi faol.")
    exam_questions = list(
        exam.exam_questions.select_related("question__subject", "question__topic")
        .prefetch_related("question__skills", "question__options")
    )
    if not exam_questions:
        raise ValidationError("Imtihonda savollar mavjud emas.")

    answers = {
        answer.exam_question_id: answer
        for answer in attempt.answers.select_related("selected_option")
    }
    subject_data = defaultdict(lambda: {"earned": Decimal("0"), "possible": Decimal("0")})
    topic_data = defaultdict(lambda: {"earned": Decimal("0"), "possible": Decimal("0"), "count": 0})
    skill_data = defaultdict(lambda: {"earned": Decimal("0"), "possible": Decimal("0"), "count": 0})
    total_earned = Decimal("0")

    for exam_question in exam_questions:
        answer = answers.get(exam_question.id)
        is_correct = bool(
            answer
            and answer.selected_option.question_id == exam_question.question_id
            and answer.selected_option.is_correct
        )
        earned = exam_question.points if is_correct else Decimal("0")
        if answer:
            answer.is_correct = is_correct
            answer.earned_points = earned
            answer.save(update_fields=["is_correct", "earned_points"])
        total_earned += earned
        subject_id = exam_question.question.subject_id
        topic_id = exam_question.question.topic_id
        subject_data[subject_id]["possible"] += exam_question.points
        subject_data[subject_id]["earned"] += earned
        topic_data[topic_id]["possible"] += exam_question.points
        topic_data[topic_id]["earned"] += earned
        topic_data[topic_id]["count"] += 1
        for skill in exam_question.question.skills.all():
            skill_data[skill.id]["possible"] += exam_question.points
            skill_data[skill.id]["earned"] += earned
            skill_data[skill.id]["count"] += 1

    weights = {item.subject_id: item for item in exam.subject_weights.select_related("subject")}
    subject_scores = {}
    weighted_score = Decimal("0")
    for subject_id, data in subject_data.items():
        score = rounded((data["earned"] / data["possible"] * 100) if data["possible"] else 0)
        subject_scores[subject_id] = score
        weight = weights.get(subject_id)
        weight_percent = weight.weight_percent if weight else Decimal("0")
        weighted_score += score * weight_percent / 100

    # If weights were not configured, fall back to a simple average instead of returning zero.
    if subject_scores and not any(item.weight_percent for item in weights.values()):
        weighted_score = sum(subject_scores.values(), Decimal("0")) / len(subject_scores)

    overall = rounded(weighted_score)
    ready = overall >= exam.readiness_threshold and all(
        score >= exam.minimum_subject_score for score in subject_scores.values()
    )
    attempt.status = ExamAttempt.Status.EXPIRED if timezone.now() > attempt.expires_at else ExamAttempt.Status.SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.submitted_by = submitted_by
    attempt.earned_points = total_earned
    attempt.overall_score = overall
    attempt.is_ready = ready
    attempt.save(update_fields=[
        "status", "submitted_at", "submitted_by", "earned_points", "overall_score", "is_ready",
    ])
    attempt.assignment.is_active = False
    attempt.assignment.save(update_fields=["is_active"])

    report, _ = DiagnosticReport.objects.update_or_create(
        attempt=attempt,
        defaults={
            "overall_score": overall,
            "range_low": max(Decimal("0"), overall - 3),
            "range_high": min(Decimal("100"), overall + 3),
            "expected_score": overall,
            "readiness": DiagnosticReport.Readiness.READY if ready else DiagnosticReport.Readiness.NOT_READY,
            "summary": "Eng past ko‘rsatkichlardan boshlab prerequisite tartibida ishlash tavsiya qilinadi.",
        },
    )
    report.subject_results.all().delete()
    report.topic_results.all().delete()
    report.skill_results.all().delete()

    SubjectResult.objects.bulk_create([
        SubjectResult(
            report=report,
            subject_id=subject_id,
            earned_points=data["earned"],
            possible_points=data["possible"],
            score=subject_scores[subject_id],
            weight_percent=weights.get(subject_id).weight_percent if weights.get(subject_id) else 0,
            level=subject_level(weights[subject_id].subject.slug, subject_scores[subject_id])
            if weights.get(subject_id)
            else score_level(subject_scores[subject_id]),
            percentile=max(1, min(99, int(subject_scores[subject_id] * Decimal("0.82")))),
            potential=min(100, int(subject_scores[subject_id] + (100 - subject_scores[subject_id]) * Decimal("0.55"))),
        )
        for subject_id, data in subject_data.items()
    ])
    TopicResult.objects.bulk_create([
        TopicResult(
            report=report,
            topic_id=topic_id,
            earned_points=data["earned"],
            possible_points=data["possible"],
            score=rounded((data["earned"] / data["possible"] * 100) if data["possible"] else 0),
            question_count=data["count"],
            confidence=confidence_for(data["count"]),
        )
        for topic_id, data in topic_data.items()
    ])
    SkillResult.objects.bulk_create([
        SkillResult(
            report=report,
            skill_id=skill_id,
            earned_points=data["earned"],
            possible_points=data["possible"],
            score=rounded((data["earned"] / data["possible"] * 100) if data["possible"] else 0),
            question_count=data["count"],
            confidence=confidence_for(data["count"]),
        )
        for skill_id, data in skill_data.items()
    ])

    profile = getattr(attempt.assignment.student, "student_profile", None)
    if profile:
        profile.status = profile.Status.DIAGNOSED
        profile.save(update_fields=["status", "updated_at"])
    build_roadmap(report)
    return report


@transaction.atomic
def build_roadmap(report: DiagnosticReport) -> Roadmap:
    student = report.attempt.assignment.student
    profile = getattr(student, "student_profile", None)
    primary_goal = None
    categories = []
    weekly_hours = 5
    target_score = 85
    interview_summary = ""

    if profile:
        primary_goal = profile.goals.filter(is_primary=True, is_active=True).first()
        if not primary_goal:
            primary_goal = profile.goals.filter(is_active=True).order_by("priority").first()
        categories = list(
            profile.category_links.filter(is_active=True).values_list("category__title", flat=True)
        )
        weekly_hours = max(1, profile.weekly_study_hours)
        if primary_goal and primary_goal.target_score:
            target_score = primary_goal.target_score
        interview = profile.interviews.filter(status="completed").order_by("-completed_at").first()
        if interview:
            interview_summary = interview.admin_summary

    generation_context = {
        "grade": profile.grade if profile else None,
        "weekly_study_hours": weekly_hours,
        "goal": primary_goal.title if primary_goal else None,
        "categories": categories,
        "interview_summary": interview_summary,
    }
    roadmap, _ = Roadmap.objects.update_or_create(
        report=report,
        defaults={
            "student": student,
            "primary_goal": primary_goal,
            "target_score": target_score,
            "weekly_hours": weekly_hours,
            "generation_context": generation_context,
            "status": Roadmap.Status.DRAFT,
        },
    )
    roadmap.stages.all().delete()
    weakest_topics = list(
        report.topic_results.select_related("topic__subject").order_by("score", "-question_count")[:3]
    )
    if not weakest_topics:
        return roadmap

    current = int(report.overall_score)
    month_ranges = [(0, 3), (3, 6), (6, 12)]
    target_candidates = [min(60, current + 20), min(75, current + 35), target_score]
    per_stage_hours = max(1, round(weekly_hours / len(weakest_topics)))
    created_stages = []
    for index, topic_result in enumerate(weakest_topics):
        start_month, end_month = month_ranges[index]
        start_score = current if index == 0 else target_candidates[index - 1]
        stage = RoadmapStage.objects.create(
            roadmap=roadmap,
            subject=topic_result.topic.subject,
            focus_topic=topic_result.topic,
            order=index + 1,
            title=topic_result.topic.title,
            start_month=start_month,
            end_month=end_month,
            start_score=start_score,
            target_score=target_candidates[index],
            weekly_hours=per_stage_hours,
            rationale=(
                f"Diagnostikada {topic_result.score}/100. "
                f"Asosiy maqsad: {primary_goal.title if primary_goal else 'umumiy rivojlanish'}. "
                f"Admin kategoriyalari: {', '.join(categories) if categories else 'belgilanmagan'}."
            ),
        )
        created_stages.append(stage)

    first = created_stages[0]
    weekly_copy = [
        (1, "Asosiy tushuncha", "Qisqa video va 15 ta boshlang‘ich mashq"),
        (2, "Chuqurlashtirish", "Real masalalar va ko‘p bosqichli topshiriqlar"),
        (3, "Mustahkamlash", "20 ta aralash mashq va xato daftari"),
        (4, "Prerequisite nazorati", "Bog‘liq poydevor mavzularni tekshirish"),
        (5, "Umumiy takror", "Oldingi fokuslardan aralash mashq"),
        (6, "Mini-diagnostika", "Natijani qayta o‘lchash va roadmapni yangilash"),
    ]
    WeeklyTask.objects.bulk_create([
        WeeklyTask(
            stage=first,
            week_number=week,
            audience=WeeklyTask.Audience.STUDENT,
            title=title,
            description=description,
        )
        for week, title, description in weekly_copy
    ])
    WeeklyTask.objects.create(
        stage=first,
        week_number=1,
        audience=WeeklyTask.Audience.TEACHER,
        title="Fokus dars",
        description="Darsda fokus mavzuga 10 daqiqa ajrating va progressni kuzating.",
    )
    WeeklyTask.objects.create(
        stage=first,
        week_number=1,
        audience=WeeklyTask.Audience.PARENT,
        title="O‘qish ritmi",
        description="Kunlik mashq vaqtini kalendarga kiriting va xato daftarini haftada bir ko‘ring.",
    )
    if profile:
        profile.status = profile.Status.ROADMAP_DRAFT
        profile.save(update_fields=["status", "updated_at"])
    return roadmap


def start_attempt(assignment, started_by=None):
    if not is_enabled_diagnostic_exam(assignment.exam):
        raise ValidationError("Hozircha faqat English diagnostik testi faol.")
    existing = assignment.attempts.filter(status=ExamAttempt.Status.IN_PROGRESS).first()
    if existing:
        return existing
    if assignment.attempts.filter(status=ExamAttempt.Status.SUBMITTED).exists():
        raise ValidationError("Bu imtihon uchun urinish allaqachon yakunlangan.")
    question_order = list(
        assignment.exam.exam_questions.order_by("order", "id").values_list("id", flat=True)
    )
    SystemRandom().shuffle(question_order)
    return ExamAttempt.objects.create(
        assignment=assignment,
        started_by=started_by,
        expires_at=timezone.now() + timedelta(minutes=assignment.exam.duration_minutes),
        question_order=question_order,
    )
