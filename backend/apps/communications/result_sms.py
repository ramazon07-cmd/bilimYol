import logging
from decimal import Decimal

from .eskiz import EskizError, send_sms
from .services import family_users


logger = logging.getLogger(__name__)


def format_score(score) -> str:
    value = Decimal(str(score))

    if value == value.to_integral():
        return str(int(value))

    return f"{value:.2f}".rstrip("0").rstrip(".")


def send_result_sms(
    *,
    student,
    score,
    exam_title: str,
) -> dict:
    phones = set()

    parents = family_users(student, include_student=False)

    for parent in parents:
        if parent.phone:
            phones.add(parent.phone)

    # Parent bo'lmasa studentning telefoniga yuborish
    if not phones and student.phone:
        phones.add(student.phone)


    message = (
        f"BilimYol: {student.full_name} "
        f"{exam_title} testidan {format_score(score)}/100 ball oldi. "
        "Batafsil natija BilimYol platformasida."
    )

    sent = 0
    failed = 0

    for phone in phones:
        try:
            send_sms(phone, message)
            sent += 1
        except EskizError:
            failed += 1
            logger.exception(
                "Natija SMS yuborilmadi. Student ID: %s, phone: %s",
                student.id,
                phone,
            )

    return {
        "sent": sent,
        "failed": failed,
        "recipients": len(phones),
    }