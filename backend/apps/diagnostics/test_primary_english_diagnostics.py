from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.academics.models import Exam, Question
from apps.academics.policies import is_enabled_diagnostic_exam

from .services import subject_level


@override_settings(DIAGNOSTIC_ACTIVE_SUBJECTS=("english", "math"))
class PrimaryEnglishDiagnosticSeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_primary_english_diagnostics", verbosity=0)

    def test_grades_one_to_four_receive_active_english_tests(self):
        for grade, expected_duration in ((1, 30), (2, 30), (3, 40), (4, 40)):
            exam = Exam.objects.get(title=f"RBIS English Placement - {grade}-sinf")
            self.assertEqual(exam.grade, grade)
            self.assertEqual(exam.status, Exam.Status.ACTIVE)
            self.assertEqual(exam.duration_minutes, expected_duration)
            self.assertEqual(exam.exam_questions.count(), 30)
            self.assertTrue(is_enabled_diagnostic_exam(exam))
            self.assertSetEqual(
                set(exam.subject_weights.values_list("subject__slug", flat=True)),
                {"english"},
            )

    def test_grades_one_and_two_share_test_one_bank(self):
        grade_one = Exam.objects.get(title="RBIS English Placement - 1-sinf")
        grade_two = Exam.objects.get(title="RBIS English Placement - 2-sinf")
        self.assertListEqual(
            list(grade_one.exam_questions.order_by("order").values_list("question__code", flat=True)),
            list(grade_two.exam_questions.order_by("order").values_list("question__code", flat=True)),
        )
        self.assertTrue(
            all(code.startswith("RBIS-ENG-PT1-") for code in
                grade_one.exam_questions.values_list("question__code", flat=True))
        )

    def test_grades_three_and_four_share_test_two_bank(self):
        grade_three = Exam.objects.get(title="RBIS English Placement - 3-sinf")
        grade_four = Exam.objects.get(title="RBIS English Placement - 4-sinf")
        self.assertListEqual(
            list(grade_three.exam_questions.order_by("order").values_list("question__code", flat=True)),
            list(grade_four.exam_questions.order_by("order").values_list("question__code", flat=True)),
        )
        self.assertTrue(
            all(code.startswith("RBIS-ENG-PT2-") for code in
                grade_three.exam_questions.values_list("question__code", flat=True))
        )

    def test_primary_question_banks_have_sixty_questions(self):
        self.assertEqual(Question.objects.filter(code__startswith="RBIS-ENG-PT1-").count(), 30)
        self.assertEqual(Question.objects.filter(code__startswith="RBIS-ENG-PT2-").count(), 30)

    def test_primary_cefr_conversion_uses_pdf_bands(self):
        self.assertEqual(subject_level("english", 0, grade=3), "Below A1")
        self.assertEqual(subject_level("english", 33.33, grade=3), "Below A1")
        self.assertEqual(subject_level("english", 36.67, grade=3), "A1")
        self.assertEqual(subject_level("english", 66.67, grade=3), "A1")
        self.assertEqual(subject_level("english", 70, grade=3), "A2")
        self.assertEqual(subject_level("english", 100, grade=4), "A2")

    def test_existing_senior_cefr_conversion_is_preserved(self):
        self.assertEqual(subject_level("english", 20, grade=8), "A1")
        self.assertEqual(subject_level("english", 40, grade=8), "A2")
        self.assertEqual(subject_level("english", 60, grade=8), "B1")
        self.assertEqual(subject_level("english", 80, grade=8), "B2")
        self.assertEqual(subject_level("english", 90, grade=8), "C1")


@override_settings(DIAGNOSTIC_ACTIVE_SUBJECTS=("english", "math"))
class SeniorEnglishFullDiagnosticSeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_senior_english_full_diagnostics", verbosity=0)

    def test_grades_five_to_eleven_use_the_full_test_three(self):
        for grade in range(5, 12):
            exam = Exam.objects.get(title=f"RBIS English Placement - {grade}-sinf")
            self.assertEqual(exam.duration_minutes, 50)
            self.assertEqual(exam.exam_questions.count(), 30)
            self.assertTrue(is_enabled_diagnostic_exam(exam))
            self.assertTrue(
                all(
                    code.startswith("RBIS-ENG-PT3-")
                    for code in exam.exam_questions.values_list("question__code", flat=True)
                )
            )
