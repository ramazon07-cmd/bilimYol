from decimal import Decimal

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.diagnostics.models import DiagnosticReport

from .models import Certificate, University, UniversityGoal


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ["id", "name", "country", "city", "logo_url", "target_math", "target_english", "target_iq", "target_ielts", "target_sat", "is_active"]


class CertificateSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source="student", read_only=True)
    verified_by_name = serializers.CharField(source="verified_by.full_name", read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "id", "student", "student_detail", "kind", "title", "score", "issued_at",
            "expires_at", "file_url", "is_verified", "verification_status",
            "verification_note", "reviewed_at", "verified_by", "verified_by_name", "created_at",
        ]
        read_only_fields = [
            "is_verified", "verification_status", "verification_note", "reviewed_at",
            "verified_by", "created_at",
        ]

    def validate(self, attrs):
        if self.instance and "student" in attrs and attrs["student"].id != self.instance.student_id:
            raise serializers.ValidationError({"student": "Sertifikat egasini o‘zgartirib bo‘lmaydi."})
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        score = attrs.get("score", getattr(self.instance, "score", None))
        issued_at = attrs.get("issued_at", getattr(self.instance, "issued_at", None))
        expires_at = attrs.get("expires_at", getattr(self.instance, "expires_at", None))
        if expires_at and issued_at and expires_at < issued_at:
            raise serializers.ValidationError({"expires_at": "Amal qilish sanasi berilgan sanadan oldin bo‘la olmaydi."})
        if kind == Certificate.Kind.IELTS and score is not None and not Decimal("0") <= score <= Decimal("9"):
            raise serializers.ValidationError({"score": "IELTS balli 0 dan 9 gacha bo‘lishi kerak."})
        if kind == Certificate.Kind.SAT and score is not None and not Decimal("400") <= score <= Decimal("1600"):
            raise serializers.ValidationError({"score": "SAT balli 400 dan 1600 gacha bo‘lishi kerak."})
        if kind == Certificate.Kind.CEFR and score is not None and not Decimal("0") <= score <= Decimal("100"):
            raise serializers.ValidationError({"score": "CEFR natijasi 0 dan 100 gacha bo‘lishi kerak."})
        return attrs


class UniversityGoalSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source="student", read_only=True)
    university_detail = UniversitySerializer(source="university", read_only=True)
    selected_by_name = serializers.CharField(source="selected_by.full_name", read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = UniversityGoal
        fields = ["id", "student", "student_detail", "university", "university_detail", "target_year", "selected_by", "selected_by_name", "progress", "selected_at", "updated_at"]
        read_only_fields = ["selected_by", "selected_at", "updated_at"]

    def validate(self, attrs):
        if self.instance and "student" in attrs and attrs["student"].id != self.instance.student_id:
            raise serializers.ValidationError({"student": "Universitet maqsadi egasini o‘zgartirib bo‘lmaydi."})
        return attrs

    @staticmethod
    def _percent(current, target):
        if not target:
            return 0
        return round(min(Decimal("100"), Decimal(str(current)) / Decimal(str(target)) * Decimal("100")), 1)

    def get_progress(self, goal):
        latest = (
            DiagnosticReport.objects.filter(attempt__assignment__student=goal.student)
            .prefetch_related("subject_results__subject")
            .order_by("-generated_at")
            .first()
        )
        subject_scores = {}
        if latest:
            subject_scores = {item.subject.slug: Decimal(item.score) for item in latest.subject_results.all()}
        math_score = subject_scores.get("math", Decimal("0"))
        english_score = subject_scores.get("english", Decimal("0"))
        iq_score = subject_scores.get("iq", subject_scores.get("critical", Decimal("0")))

        verified = goal.student.certificates.filter(is_verified=True)
        ielts = verified.filter(kind=Certificate.Kind.IELTS).order_by("-score").first()
        sat = verified.filter(kind=Certificate.Kind.SAT).order_by("-score").first()
        university = goal.university
        requirements = [
            self._requirement("math", "Matematika mock", math_score, university.target_math, "ball", "mock"),
            self._requirement("english", "English mock", english_score, university.target_english, "ball", "mock"),
            self._requirement("iq", "IQ mock", iq_score, university.target_iq, "ball", "mock"),
            self._requirement("ielts", "IELTS sertifikati", ielts.score if ielts else 0, university.target_ielts, "band", "certificate", bool(ielts)),
            self._requirement("sat", "SAT sertifikati", sat.score if sat else 0, university.target_sat, "ball", "certificate", bool(sat)),
        ]
        overall = round(sum(float(item["progress"]) for item in requirements) / len(requirements), 1)
        return {
            "overall": overall,
            "status": "ready" if overall >= 100 else "in_progress",
            "latest_mock": latest.generated_at if latest else None,
            "latest_mock_score": float(latest.overall_score) if latest else None,
            "requirements": requirements,
        }

    def _requirement(self, key, label, current, target, unit, source, has_certificate=True):
        progress = self._percent(current, target) if has_certificate else 0
        return {
            "key": key,
            "label": label,
            "current": float(current),
            "target": float(target),
            "unit": unit,
            "source": source,
            "progress": progress,
            "complete": progress >= 100,
            "has_certificate": has_certificate if source == "certificate" else None,
        }
