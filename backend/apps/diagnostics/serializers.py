from rest_framework import serializers

from apps.accounts.serializers import ClassroomSerializer, UserSerializer
from apps.academics.serializers import ExamSerializer, SkillSerializer, SubjectSerializer, TopicSerializer

from .models import DiagnosticReport, ExamAssignment, ExamAttempt, Roadmap, RoadmapStage, SkillResult, StudentAnswer, SubjectResult, TopicResult, WeeklyTask


class AssignmentSerializer(serializers.ModelSerializer):
    exam_detail = ExamSerializer(source="exam", read_only=True)
    student_detail = UserSerializer(source="student", read_only=True)
    classroom_detail = ClassroomSerializer(source="classroom", read_only=True)
    has_attempt = serializers.SerializerMethodField()

    class Meta:
        model = ExamAssignment
        fields = ["id", "exam", "exam_detail", "classroom", "classroom_detail", "student", "student_detail", "available_from", "due_at", "is_active", "has_attempt", "created_at"]
        read_only_fields = ["created_at"]

    def get_has_attempt(self, obj):
        return obj.attempts.exists()


class AnswerSerializer(serializers.ModelSerializer):
    question_code = serializers.CharField(source="exam_question.question.code", read_only=True)
    selected_label = serializers.CharField(source="selected_option.label", read_only=True)

    class Meta:
        model = StudentAnswer
        fields = ["id", "exam_question", "question_code", "selected_option", "selected_label", "is_correct", "earned_points", "is_flagged", "answered_at"]
        read_only_fields = ["is_correct", "earned_points", "answered_at"]


class AttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="assignment.student.full_name", read_only=True)
    exam_title = serializers.CharField(source="assignment.exam.title", read_only=True)
    remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = ExamAttempt
        fields = ["id", "assignment", "student_name", "exam_title", "status", "started_at", "submitted_at", "expires_at", "remaining_seconds", "earned_points", "overall_score", "is_ready", "answers"]
        read_only_fields = ["status", "started_at", "submitted_at", "expires_at", "earned_points", "overall_score", "is_ready"]

    def get_remaining_seconds(self, obj):
        from django.utils import timezone

        return max(0, int((obj.expires_at - timezone.now()).total_seconds()))


class SubjectResultSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = SubjectResult
        fields = ["id", "subject", "earned_points", "possible_points", "score", "weight_percent", "level", "percentile", "rank", "potential"]


class TopicResultSerializer(serializers.ModelSerializer):
    topic = TopicSerializer(read_only=True)

    class Meta:
        model = TopicResult
        fields = ["id", "topic", "earned_points", "possible_points", "score", "question_count", "confidence"]


class SkillResultSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)

    class Meta:
        model = SkillResult
        fields = ["id", "skill", "earned_points", "possible_points", "score", "question_count", "confidence"]


class WeeklyTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyTask
        fields = ["id", "week_number", "audience", "title", "description", "resource_url", "is_completed", "completed_at"]


class RoadmapStageSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    focus_topic = TopicSerializer(read_only=True)
    weekly_tasks = WeeklyTaskSerializer(many=True, read_only=True)

    class Meta:
        model = RoadmapStage
        fields = ["id", "subject", "focus_topic", "order", "title", "start_month", "end_month", "start_score", "target_score", "weekly_hours", "rationale", "weekly_tasks"]


class RoadmapSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source="student", read_only=True)
    teacher_detail = UserSerializer(source="teacher", read_only=True)
    stages = RoadmapStageSerializer(many=True, read_only=True)

    class Meta:
        model = Roadmap
        fields = ["id", "report", "student", "student_detail", "teacher", "teacher_detail", "target_score", "weekly_hours", "status", "approved_at", "stages", "created_at", "updated_at"]
        read_only_fields = ["report", "student", "teacher", "approved_at", "created_at", "updated_at"]


class DiagnosticReportSerializer(serializers.ModelSerializer):
    subject_results = SubjectResultSerializer(many=True, read_only=True)
    topic_results = TopicResultSerializer(many=True, read_only=True)
    skill_results = SkillResultSerializer(many=True, read_only=True)
    roadmap = RoadmapSerializer(read_only=True)
    student = UserSerializer(source="attempt.assignment.student", read_only=True)
    exam = ExamSerializer(source="attempt.assignment.exam", read_only=True)

    class Meta:
        model = DiagnosticReport
        fields = ["id", "attempt", "student", "exam", "overall_score", "range_low", "range_high", "expected_score", "readiness", "summary", "subject_results", "topic_results", "skill_results", "roadmap", "generated_at"]
