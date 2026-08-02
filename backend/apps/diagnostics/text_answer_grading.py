from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
import unicodedata

from rest_framework.exceptions import ValidationError

from .models import StudentAnswer


_TRANSLATION = str.maketrans({
    "−": "-",
    "–": "-",
    "—": "-",
    "×": "x",
    "÷": "/",
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
})

_DECIMAL_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
_FRACTION_RE = re.compile(
    r"^(?P<num>[+-]?(?:\d+(?:\.\d*)?|\.\d+))/"
    r"(?P<den>[+-]?(?:\d+(?:\.\d*)?|\.\d+))$"
)


def accepted_answers(question) -> list[str]:
    return [
        item.strip()
        for item in str(question.accepted_text_answers or "").splitlines()
        if item.strip()
    ]


def normalize_text_answer(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.translate(_TRANSLATION).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def compact_text_answer(value: str) -> str:
    return re.sub(r"\s+", "", normalize_text_answer(value))


def decimal_answer(value: str) -> Decimal | None:
    raw = compact_text_answer(value).replace(",", ".")
    try:
        if _DECIMAL_RE.fullmatch(raw):
            return Decimal(raw)
        match = _FRACTION_RE.fullmatch(raw)
        if match:
            denominator = Decimal(match.group("den"))
            if denominator == 0:
                return None
            return Decimal(match.group("num")) / denominator
    except (InvalidOperation, ZeroDivisionError):
        return None
    return None


def text_answer_matches(question, submitted: str) -> bool:
    submitted_normalized = normalize_text_answer(submitted)
    submitted_compact = compact_text_answer(submitted)
    submitted_number = decimal_answer(submitted)
    tolerance = Decimal(question.answer_tolerance or 0)

    for expected in accepted_answers(question):
        if submitted_normalized == normalize_text_answer(expected):
            return True
        if submitted_compact == compact_text_answer(expected):
            return True

        expected_number = decimal_answer(expected)
        if submitted_number is not None and expected_number is not None:
            if abs(submitted_number - expected_number) <= tolerance:
                return True

    return False


def grade_attempt_from_answer_key(attempt) -> bool:
    exam_questions = list(
        attempt.assignment.exam.exam_questions.select_related("question")
        .order_by("order", "id")
    )

    if any(not accepted_answers(item.question) for item in exam_questions):
        return False

    answers_by_question = {
        answer.exam_question_id: answer
        for answer in attempt.answers.select_related(
            "selected_option", "exam_question__question"
        )
    }

    updates = []
    for exam_question in exam_questions:
        answer = answers_by_question.get(exam_question.id)
        if (
            answer is None
            or answer.selected_option.label != "TEXT"
            or not answer.text_answer.strip()
        ):
            raise ValidationError(
                f"{exam_question.question.code} savoliga yozma javob topilmadi."
            )

        is_correct = text_answer_matches(
            exam_question.question,
            answer.text_answer,
        )
        earned = exam_question.points if is_correct else Decimal("0")
        answer.manual_score = earned
        answer.is_graded = True
        answer.is_correct = is_correct
        answer.earned_points = earned
        updates.append(answer)

    if updates:
        StudentAnswer.objects.bulk_update(
            updates,
            [
                "manual_score",
                "is_graded",
                "is_correct",
                "earned_points",
            ],
            batch_size=200,
        )
    return True
