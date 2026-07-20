from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Classroom, ClassroomStudent, ParentStudent
from apps.academics.models import Exam, ExamQuestion, ExamSubjectWeight, Question, QuestionOption, Skill, Subject, Topic
from apps.diagnostics.models import ExamAssignment, ExamAttempt, StudentAnswer
from apps.diagnostics.services import submit_attempt
from apps.pathways.models import Certificate, University, UniversityGoal


User = get_user_model()


class Command(BaseCommand):
    help = "BilimYo‘l uchun to‘liq demo dataset yaratadi"

    def handle(self, *args, **options):
        admin = self.user("admin", "Admin BilimYo‘l", User.Role.ADMIN, "admin12345", is_staff=True, is_superuser=True)
        teacher = self.user("teacher", "Dilnoza Usmonova", User.Role.TEACHER, "teacher123")
        student = self.user("student", "Bobur Xasanboyev", User.Role.STUDENT, "student123")
        parent = self.user("parent", "Otabek Xasanboyev", User.Role.PARENT, "parent123")

        classrooms = {}
        for grade in range(5, 10):
            classrooms[grade], _ = Classroom.objects.update_or_create(
                name=f"{grade}-A",
                defaults={"grade": grade, "program": "Prezident maktabiga tayyorgarlik", "teacher": teacher, "is_active": True},
            )
        classroom = classrooms[8]
        ClassroomStudent.objects.get_or_create(classroom=classroom, student=student)
        ParentStudent.objects.get_or_create(parent=parent, student=student, defaults={"relationship": "Ota"})

        subject_specs = [
            ("math", "Matematika", "#c8564e"),
            ("english", "Ingliz tili", "#d99a16"),
            ("iq", "IQ", "#4568a8"),
        ]
        subjects = {}
        for order, (slug, title, color) in enumerate(subject_specs, 1):
            subjects[slug], _ = Subject.objects.update_or_create(slug=slug, defaults={"title": title, "color": color, "order": order, "is_active": True})

        topic_specs = {
            "math": ["Daraja xossalari", "Qisqa ko‘paytirish formulalari", "Geometrik burchaklar", "Tenglamalar"],
            "english": ["Main idea", "Context vocabulary", "Inferensial o‘qish", "Grammar in context"],
            "iq": ["Oddiy ketma-ketlik", "Shartli mulohaza", "Analogiya", "Dalilni baholash"],
        }
        skill_specs = {
            "math": ["Algebraik fikrlash", "Konseptual tushunish", "Hisoblash aniqligi", "Geometrik-fazoviy tafakkur", "Mantiqiy mulohaza", "Masalani modellashtirish", "Muammoni yechish"],
            "english": ["Faktik o‘qish", "Inferensial o‘qish", "Leksik tahlil", "Matn strukturasi", "Grammatik aniqlik", "Tanqidiy o‘qish", "Xulosa chiqarish"],
            "iq": ["Qonuniyatni topish", "Mantiqiy xulosa", "Tasniflash", "Fazoviy qonuniyat", "Dalilni baholash", "Qarshi misol", "Muammoni yechish"],
        }
        topics, skills = {}, {}
        for slug, titles in topic_specs.items():
            topics[slug] = []
            for order, title in enumerate(titles, 1):
                topic, _ = Topic.objects.update_or_create(subject=subjects[slug], code=f"{slug[:1].upper()}T{order}", defaults={"title": title, "order": order, "healthy_threshold": 75})
                topics[slug].append(topic)
            for index in range(1, len(topics[slug])):
                topics[slug][index].prerequisites.add(topics[slug][index - 1])
            skills[slug] = []
            for order, title in enumerate(skill_specs[slug], 1):
                skill, _ = Skill.objects.update_or_create(subject=subjects[slug], slug=f"{slug}-skill-{order}", defaults={"title": title, "order": order})
                skills[slug].append(skill)

        prompts = {
            "math": [
                ("M1", "2³ · 2² ifodaning qiymati nechaga teng?", ["32", "16", "64", "8"]),
                ("M2", "(x + 3)² ning to‘g‘ri yoyilmasini toping.", ["x² + 6x + 9", "x² + 9", "x² + 3x + 9", "x² + 6"]),
                ("M3", "Vertikal burchaklardan biri 70° bo‘lsa, ikkinchisi nechaga teng?", ["70°", "110°", "35°", "140°"]),
                ("M4", "2x + 5 = 13 tenglamani yeching.", ["x = 4", "x = 9", "x = 3", "x = 6"]),
            ],
            "english": [
                ("E1", "Choose the main idea of the paragraph.", ["The central message", "A minor detail", "The title only", "An unrelated fact"]),
                ("E2", "Choose the closest meaning of ‘significant’.", ["Important", "Tiny", "Optional", "Ordinary"]),
                ("E3", "What can be inferred from the author’s statement?", ["The supported conclusion", "A direct quote", "An unrelated claim", "No conclusion"]),
                ("E4", "Choose the grammatically correct sentence.", ["She has finished her work.", "She have finish her work.", "She finishing work.", "She has finish work."]),
            ],
            "iq": [
                ("T1", "2, 4, 8, 16 ketma-ketligining keyingi sonini toping.", ["32", "24", "18", "20"]),
                ("T2", "Barcha olimlar o‘qiydi. Nodir olim. Aniq xulosani toping.", ["Nodir o‘qiydi", "Nodir yozuvchi", "Barcha o‘quvchilar olim", "Nodir faqat ilmiy kitob o‘qiydi"]),
                ("T3", "Qalam : yozish = qaychi : ?", ["Kesish", "O‘qish", "Bo‘yash", "Sanash"]),
                ("T4", "Qaysi dalil berilgan xulosani eng kuchli qo‘llab-quvvatlaydi?", ["Bevosita ishonchli dalil", "Shaxsiy taxmin", "Mavzuga aloqasiz fakt", "Takrorlangan fikr"]),
            ],
        }
        questions = []
        for slug, items in prompts.items():
            for index, (code, prompt, options_text) in enumerate(items):
                question, _ = Question.objects.update_or_create(
                    code=code,
                    defaults={
                        "subject": subjects[slug],
                        "topic": topics[slug][index],
                        "prompt": prompt,
                        "explanation": "To‘g‘ri javob mavzuning asosiy qoidasiga tayanadi.",
                        "difficulty": Question.Difficulty.BASIC if index == 0 else Question.Difficulty.MEDIUM if index < 3 else Question.Difficulty.HIGH,
                        "default_points": 25,
                        "is_active": True,
                        "created_by": admin,
                    },
                )
                question.skills.set([skills[slug][index % len(skills[slug])]])
                question.options.all().delete()
                QuestionOption.objects.bulk_create([
                    QuestionOption(question=question, label=chr(65 + option_index), text=text, is_correct=option_index == 0, order=option_index)
                    for option_index, text in enumerate(options_text)
                ])
                questions.append(question)

        exam, _ = Exam.objects.update_or_create(
            title="8-A · IQ / Math / English Mock #1",
            defaults={
                "grade": 8,
                "description": "8-sinf uchun IQ, Matematika va English diagnostik testi — har bir fan 100 ballik.",
                "duration_minutes": 90,
                "max_score": 100,
                "readiness_threshold": 67,
                "minimum_subject_score": 50,
                "starts_at": timezone.now() - timedelta(days=2),
                "ends_at": timezone.now() + timedelta(days=30),
                "status": Exam.Status.ACTIVE,
                "created_by": admin,
            },
        )
        exam.target_classrooms.set([classroom])
        exam.subject_weights.all().delete()
        ExamSubjectWeight.objects.bulk_create([
            ExamSubjectWeight(exam=exam, subject=subjects["math"], weight_percent=35, max_score=100),
            ExamSubjectWeight(exam=exam, subject=subjects["english"], weight_percent=35, max_score=100),
            ExamSubjectWeight(exam=exam, subject=subjects["iq"], weight_percent=30, max_score=100),
        ])
        exam.exam_questions.all().delete()
        exam_questions = [ExamQuestion.objects.create(exam=exam, question=question, points=25, order=index + 1) for index, question in enumerate(questions)]

        for grade, target_classroom in classrooms.items():
            if grade == 8:
                continue
            grade_exam, _ = Exam.objects.update_or_create(
                title=f"{grade}-sinf · IQ / Math / English Mock #1",
                defaults={
                    "grade": grade,
                    "description": f"{grade}-sinfga moslashtirilgan uch fan testi. Har bir fan 100 ballik shkala bilan tahlil qilinadi.",
                    "duration_minutes": 75 if grade < 7 else 90,
                    "max_score": 100,
                    "readiness_threshold": 67,
                    "minimum_subject_score": 50,
                    "starts_at": timezone.now(),
                    "ends_at": timezone.now() + timedelta(days=30),
                    "status": Exam.Status.ACTIVE,
                    "created_by": admin,
                },
            )
            grade_exam.target_classrooms.set([target_classroom])
            grade_exam.subject_weights.all().delete()
            ExamSubjectWeight.objects.bulk_create([
                ExamSubjectWeight(exam=grade_exam, subject=subjects["iq"], weight_percent=30, max_score=100),
                ExamSubjectWeight(exam=grade_exam, subject=subjects["math"], weight_percent=35, max_score=100),
                ExamSubjectWeight(exam=grade_exam, subject=subjects["english"], weight_percent=35, max_score=100),
            ])
            grade_exam.exam_questions.all().delete()
            ExamQuestion.objects.bulk_create([
                ExamQuestion(exam=grade_exam, question=question, points=25, order=index + 1)
                for index, question in enumerate(questions)
            ])
        assignment, _ = ExamAssignment.objects.update_or_create(exam=exam, student=student, defaults={"classroom": classroom, "is_active": True, "assigned_by": teacher, "due_at": timezone.now() + timedelta(days=7)})

        if not assignment.attempts.filter(status=ExamAttempt.Status.SUBMITTED).exists():
            attempt = ExamAttempt.objects.create(assignment=assignment, expires_at=timezone.now() + timedelta(minutes=90))
            correct_indexes = {0, 4, 5, 8, 9}
            for index, exam_question in enumerate(exam_questions):
                selected = exam_question.question.options.get(label="A" if index in correct_indexes else "B")
                StudentAnswer.objects.create(attempt=attempt, exam_question=exam_question, selected_option=selected)
            submit_attempt(attempt)

        stanford, _ = University.objects.update_or_create(
            name="Stanford University",
            defaults={
                "country": "AQSh",
                "city": "Stanford, California",
                "target_math": 90,
                "target_english": 85,
                "target_iq": 85,
                "target_ielts": 7.0,
                "target_sat": 1500,
                "is_active": True,
            },
        )
        University.objects.update_or_create(
            name="National University of Singapore",
            defaults={"country": "Singapur", "city": "Singapore", "target_math": 88, "target_english": 82, "target_iq": 82, "target_ielts": 6.5, "target_sat": 1450, "is_active": True},
        )
        University.objects.update_or_create(
            name="KAIST",
            defaults={"country": "Janubiy Koreya", "city": "Daejeon", "target_math": 90, "target_english": 78, "target_iq": 88, "target_ielts": 6.5, "target_sat": 1450, "is_active": True},
        )
        UniversityGoal.objects.update_or_create(
            student=student,
            defaults={"university": stanford, "target_year": timezone.now().year + 4, "selected_by": parent},
        )
        Certificate.objects.update_or_create(
            student=student,
            kind=Certificate.Kind.IELTS,
            title="IELTS Academic",
            defaults={"score": 7.0, "issued_at": timezone.localdate() - timedelta(days=40), "is_verified": True, "verified_by": admin},
        )
        Certificate.objects.update_or_create(
            student=student,
            kind=Certificate.Kind.SAT,
            title="SAT",
            defaults={"score": 1490, "issued_at": timezone.localdate() - timedelta(days=20), "is_verified": True, "verified_by": admin},
        )

        self.stdout.write(self.style.SUCCESS("Demo tayyor: admin/admin12345, teacher/teacher123, student/student123, parent/parent123"))

    def user(self, username, full_name, role, password, **flags):
        user, _ = User.objects.update_or_create(username=username, defaults={"full_name": full_name, "role": role, "email": f"{username}@bilimyol.uz", **flags})
        user.set_password(password)
        user.save()
        return user
