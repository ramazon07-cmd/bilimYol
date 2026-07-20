from collections import defaultdict
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import DiagnosticReport, ExamAttempt, Roadmap, RoadmapStage, SkillResult, SubjectResult, TopicResult, WeeklyTask


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


def confidence_for(question_count: int) -> str:
    if question_count >= 5:
        return "high"
    if question_count >= 3:
        return "medium"
    return "low"


@transaction.atomic
def submit_attempt(attempt: ExamAttempt) -> DiagnosticReport:
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        raise ValidationError("Bu urinish allaqachon yakunlangan.")

    exam = attempt.assignment.exam
    exam_questions = list(exam.exam_questions.select_related("question__subject", "question__topic").prefetch_related("question__skills", "question__options"))
    answers = {answer.exam_question_id: answer for answer in attempt.answers.select_related("selected_option")}

    subject_data = defaultdict(lambda: {"earned": Decimal("0"), "possible": Decimal("0")})
    topic_data = defaultdict(lambda: {"earned": Decimal("0"), "possible": Decimal("0"), "count": 0})
    skill_data = defaultdict(lambda: {"earned": Decimal("0"), "possible": Decimal("0"), "count": 0})
    total_earned = Decimal("0")

    for exam_question in exam_questions:
        answer = answers.get(exam_question.id)
        is_correct = bool(answer and answer.selected_option.question_id == exam_question.question_id and answer.selected_option.is_correct)
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

    overall = rounded(weighted_score)
    ready = overall >= exam.readiness_threshold and all(score >= exam.minimum_subject_score for score in subject_scores.values())
    attempt.status = ExamAttempt.Status.EXPIRED if timezone.now() > attempt.expires_at else ExamAttempt.Status.SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.earned_points = total_earned
    attempt.overall_score = overall
    attempt.is_ready = ready
    attempt.save(update_fields=["status", "submitted_at", "earned_points", "overall_score", "is_ready"])

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

    subject_results = []
    for subject_id, data in subject_data.items():
        score = subject_scores[subject_id]
        weight = weights.get(subject_id)
        subject_results.append(SubjectResult(
            report=report,
            subject_id=subject_id,
            earned_points=data["earned"],
            possible_points=data["possible"],
            score=score,
            weight_percent=weight.weight_percent if weight else 0,
            level=score_level(score),
            percentile=max(1, min(99, int(score * Decimal("0.82")))),
            potential=min(100, int(score + (100 - score) * Decimal("0.55"))),
        ))
    SubjectResult.objects.bulk_create(subject_results)

    TopicResult.objects.bulk_create([
        TopicResult(
            report=report,
            topic_id=topic_id,
            earned_points=data["earned"],
            possible_points=data["possible"],
            score=rounded((data["earned"] / data["possible"] * 100) if data["possible"] else 0),
            question_count=data["count"],
            confidence=confidence_for(data["count"]),
        ) for topic_id, data in topic_data.items()
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
        ) for skill_id, data in skill_data.items()
    ])
    build_roadmap(report)
    return report


@transaction.atomic
def build_roadmap(report: DiagnosticReport) -> Roadmap:
    student = report.attempt.assignment.student
    roadmap, _ = Roadmap.objects.update_or_create(report=report, defaults={"student": student, "target_score": 85, "weekly_hours": 5, "status": Roadmap.Status.DRAFT})
    roadmap.stages.all().delete()
    weakest_topics = list(report.topic_results.select_related("topic__subject").order_by("score", "-question_count")[:3])
    if not weakest_topics:
        return roadmap
    current = int(report.overall_score)
    month_ranges = [(0, 3), (3, 6), (6, 12)]
    targets = [min(60, current + 20), min(75, current + 35), 85]
    created_stages = []
    for index, topic_result in enumerate(weakest_topics):
        start_month, end_month = month_ranges[index]
        start_score = current if index == 0 else targets[index - 1]
        stage = RoadmapStage.objects.create(
            roadmap=roadmap,
            subject=topic_result.topic.subject,
            focus_topic=topic_result.topic,
            order=index + 1,
            title=topic_result.topic.title,
            start_month=start_month,
            end_month=end_month,
            start_score=start_score,
            target_score=targets[index],
            weekly_hours=5 if index == 0 else 4,
            rationale=f"Diagnostikada {topic_result.score}/100; sog‘lom chegara {topic_result.topic.healthy_threshold}.",
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
    WeeklyTask.objects.bulk_create([WeeklyTask(stage=first, week_number=week, audience=WeeklyTask.Audience.STUDENT, title=title, description=description) for week, title, description in weekly_copy])
    WeeklyTask.objects.create(stage=first, week_number=1, audience=WeeklyTask.Audience.TEACHER, title="Fokus dars", description="Darsda fokus mavzuga 10 daqiqa ajrating va progressni kuzating.")
    WeeklyTask.objects.create(stage=first, week_number=1, audience=WeeklyTask.Audience.PARENT, title="O‘qish ritmi", description="Kunlik mashq vaqtini kalendarga kiriting va xato daftarini haftada bir ko‘ring.")
    return roadmap


def start_attempt(assignment):
    existing = assignment.attempts.filter(status=ExamAttempt.Status.IN_PROGRESS).first()
    if existing:
        return existing
    if assignment.attempts.filter(status=ExamAttempt.Status.SUBMITTED).exists():
        raise ValidationError("Bu imtihon uchun urinish allaqachon yakunlangan.")
    return ExamAttempt.objects.create(assignment=assignment, expires_at=timezone.now() + timedelta(minutes=assignment.exam.duration_minutes))
