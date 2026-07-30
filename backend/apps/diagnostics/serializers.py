from rest_framework import serializers

from apps.accounts.serializers import ClassroomSerializer, UserSerializer
from apps.academics.policies import is_enabled_diagnostic_exam
from apps.academics.serializers import ExamSerializer, SkillSerializer, SubjectSerializer, TopicSerializer

from .models import (
    DiagnosticReport,
    ExamAssignment,
    ExamAttempt,
    Roadmap,
    RoadmapStage,
    SkillResult,
    StudentAnswer,
    SubjectResult,
    TopicResult,
    WeeklyTask,
)


class AssignmentSerializer(serializers.ModelSerializer):
    exam_detail = ExamSerializer(source="exam", read_only=True)
    student_detail = UserSerializer(source="student", read_only=True)
    classroom_detail = ClassroomSerializer(source="classroom", read_only=True)
    has_attempt = serializers.SerializerMethodField()

    class Meta:
        model = ExamAssignment
        fields = [
            "id", "exam", "exam_detail", "classroom", "classroom_detail", "student",
            "student_detail", "available_from", "due_at", "is_active", "delivery_mode",
            "administered_by", "has_attempt", "created_at",
        ]
        read_only_fields = ["administered_by", "created_at"]

    def get_has_attempt(self, obj):
        return obj.attempts.exists()

    def validate_exam(self, exam):
        if not is_enabled_diagnostic_exam(exam):
            raise serializers.ValidationError(
                "Hozircha faqat English savollaridan iborat diagnostik test faol."
            )
        return exam

    def validate_delivery_mode(self, value):
        if value != ExamAssignment.DeliveryMode.SELF:
            raise serializers.ValidationError(
                "Diagnostikani o‘quvchi o‘z login va paroli orqali topshiradi."
            )
        return value


class AnswerSerializer(serializers.ModelSerializer):
    question_code = serializers.CharField(source="exam_question.question.code", read_only=True)
    selected_label = serializers.CharField(source="selected_option.label", read_only=True)

    class Meta:
        model = StudentAnswer
        fields = [
            "id", "exam_question", "question_code", "selected_option", "selected_label",
            "is_correct", "earned_points", "is_flagged", "answered_at",
        ]
        read_only_fields = ["is_correct", "earned_points", "answered_at"]


class AttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="assignment.student.full_name", read_only=True)
    exam_title = serializers.CharField(source="assignment.exam.title", read_only=True)
    remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = ExamAttempt
        fields = [
            "id", "assignment", "student_name", "exam_title", "status", "started_at",
            "submitted_at", "expires_at", "remaining_seconds", "started_by", "submitted_by",
            "earned_points", "overall_score", "is_ready", "question_order", "answers",
        ]
        read_only_fields = [
            "status", "started_at", "submitted_at", "expires_at", "started_by",
            "submitted_by", "earned_points", "overall_score", "is_ready", "question_order",
        ]

    def get_remaining_seconds(self, obj):
        from django.utils import timezone
        return max(0, int((obj.expires_at - timezone.now()).total_seconds()))


class SubjectResultSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = SubjectResult
        fields = [
            "id", "subject", "earned_points", "possible_points", "score", "weight_percent",
            "level", "percentile", "rank", "potential",
        ]


class TopicResultSerializer(serializers.ModelSerializer):
    topic = TopicSerializer(read_only=True)

    class Meta:
        model = TopicResult
        fields = [
            "id", "topic", "earned_points", "possible_points", "score", "question_count", "confidence",
        ]


class SkillResultSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)

    class Meta:
        model = SkillResult
        fields = [
            "id", "skill", "earned_points", "possible_points", "score", "question_count", "confidence",
        ]


class WeeklyTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyTask
        fields = [
            "id", "week_number", "audience", "title", "description", "resource_url",
            "is_completed", "completed_at",
        ]


class RoadmapStageSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    focus_topic = TopicSerializer(read_only=True)
    weekly_tasks = WeeklyTaskSerializer(many=True, read_only=True)

    class Meta:
        model = RoadmapStage
        fields = [
            "id", "subject", "focus_topic", "order", "title", "start_month", "end_month",
            "start_score", "target_score", "weekly_hours", "rationale", "weekly_tasks",
        ]


class RoadmapSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source="student", read_only=True)
    teacher_detail = UserSerializer(source="teacher", read_only=True)
    primary_goal_title = serializers.CharField(source="primary_goal.title", read_only=True)
    stages = RoadmapStageSerializer(many=True, read_only=True)

    class Meta:
        model = Roadmap
        fields = [
            "id", "report", "student", "student_detail", "teacher", "teacher_detail",
            "primary_goal", "primary_goal_title", "generation_context", "admin_note",
            "target_score", "weekly_hours", "status", "approved_at", "stages",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "report", "student", "teacher", "primary_goal", "generation_context",
            "approved_at", "created_at", "updated_at",
        ]


class DiagnosticReportSerializer(serializers.ModelSerializer):
    subject_results = SubjectResultSerializer(many=True, read_only=True)
    topic_results = TopicResultSerializer(many=True, read_only=True)
    skill_results = SkillResultSerializer(many=True, read_only=True)
    roadmap = RoadmapSerializer(read_only=True)
    student = UserSerializer(source="attempt.assignment.student", read_only=True)
    exam = ExamSerializer(source="attempt.assignment.exam", read_only=True)
    grade = serializers.SerializerMethodField()
    classroom = serializers.SerializerMethodField()
    answer_summary = serializers.SerializerMethodField()

    class Meta:
        model = DiagnosticReport
        fields = [
            "id", "attempt", "student", "exam", "overall_score", "range_low", "range_high",
            "expected_score", "readiness", "summary", "subject_results", "topic_results",
            "skill_results", "roadmap", "grade", "classroom", "answer_summary", "generated_at",
        ]

    def get_grade(self, obj):
        assignment = obj.attempt.assignment
        profile = getattr(assignment.student, "student_profile", None)
        return getattr(profile, "grade", None) or assignment.exam.grade

    def get_classroom(self, obj):
        assignment = obj.attempt.assignment
        classroom = assignment.classroom
        if classroom is None:
            classroom = assignment.student.classrooms.filter(is_active=True).first()
        if classroom is None:
            return None
        return {"id": classroom.id, "name": classroom.name, "grade": classroom.grade}

    def get_answer_summary(self, obj):
        attempt = obj.attempt
        exam_questions = list(attempt.assignment.exam.exam_questions.all())
        answers = list(attempt.answers.all())
        correct = sum(1 for item in answers if item.is_correct)
        answered = len(answers)
        return {
            "total": len(exam_questions),
            "correct": correct,
            "incorrect": answered - correct,
            "unanswered": max(0, len(exam_questions) - answered),
        }


class DiagnosticReportDetailSerializer(DiagnosticReportSerializer):
    attempt_detail = serializers.SerializerMethodField()
    strengths = serializers.SerializerMethodField()
    weaknesses = serializers.SerializerMethodField()
    previous_attempts = serializers.SerializerMethodField()

    class Meta(DiagnosticReportSerializer.Meta):
        fields = DiagnosticReportSerializer.Meta.fields + [
            "attempt_detail", "strengths", "weaknesses", "previous_attempts",
        ]

    def get_attempt_detail(self, obj):
        attempt = obj.attempt
        assignment = attempt.assignment
        return {
            "id": attempt.id,
            "assignment_id": assignment.id,
            "status": attempt.status,
            "started_at": attempt.started_at,
            "submitted_at": attempt.submitted_at,
            "expires_at": attempt.expires_at,
            "started_by": getattr(attempt.started_by, "full_name", None),
            "submitted_by": getattr(attempt.submitted_by, "full_name", None),
            "earned_points": attempt.earned_points,
            "delivery_mode": assignment.delivery_mode,
        }

    def _rank_result(self, obj, reverse):
        rows = []
        for item in obj.skill_results.all():
            rows.append({
                "kind": "skill",
                "title": item.skill.title,
                "subject": item.skill.subject.title,
                "score": item.score,
            })
        for item in obj.topic_results.all():
            rows.append({
                "kind": "topic",
                "title": item.topic.title,
                "subject": item.topic.subject.title,
                "score": item.score,
            })
        rows.sort(key=lambda item: float(item["score"]), reverse=reverse)
        return rows

    def get_strengths(self, obj):
        strong = [item for item in self._rank_result(obj, True) if float(item["score"]) >= 67]
        return strong[:6]

    def get_weaknesses(self, obj):
        weak = [item for item in self._rank_result(obj, False) if float(item["score"]) < 67]
        return weak[:6]

    def get_previous_attempts(self, obj):
        reports = (
            DiagnosticReport.objects.filter(attempt__assignment__student=obj.attempt.assignment.student)
            .exclude(id=obj.id)
            .select_related("attempt__assignment__exam")
            .order_by("-generated_at")[:10]
        )
        return [
            {
                "id": report.id,
                "attempt_id": report.attempt_id,
                "exam_id": report.attempt.assignment.exam_id,
                "exam_title": report.attempt.assignment.exam.title,
                "overall_score": report.overall_score,
                "readiness": report.readiness,
                "generated_at": report.generated_at,
                "same_exam": report.attempt.assignment.exam_id == obj.attempt.assignment.exam_id,
            }
            for report in reports
        ]
