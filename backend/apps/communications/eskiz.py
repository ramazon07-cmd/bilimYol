import logging
import re

import requests
from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)

TOKEN_CACHE_KEY = "eskiz_api_token"


class EskizError(Exception):
    pass


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")

    if len(digits) == 9:
        digits = f"998{digits}"

    if len(digits) != 12 or not digits.startswith("998"):
        raise EskizError("Telefon raqami 998XXXXXXXXX formatida bo‘lishi kerak.")

    return digits


def get_token(force_refresh: bool = False) -> str:
    if not force_refresh:
        cached_token = cache.get(TOKEN_CACHE_KEY)
        if cached_token:
            return cached_token

    response = requests.post(
        f"{settings.ESKIZ_API_URL}/auth/login",
        data={
            "email": settings.ESKIZ_EMAIL,
            "password": settings.ESKIZ_PASSWORD,
        },
        timeout=8,
    )

    try:
        response.raise_for_status()
        payload = response.json()
        token = payload["data"]["token"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise EskizError("Eskiz tokenini olishda xatolik.") from exc

    # Token muddati tugasa 401 orqali qayta olinadi.
    cache.set(TOKEN_CACHE_KEY, token, timeout=60 * 60)
    return token


def _send(phone: str, message: str, token: str):
    return requests.post(
        f"{settings.ESKIZ_API_URL}/message/sms/send",
        headers={
            "Authorization": f"Bearer {token}",
        },
        data={
            "mobile_phone": normalize_phone(phone),
            "message": message,
            "from": settings.ESKIZ_FROM,
        },
        timeout=8,
    )


def send_sms(phone: str, message: str) -> dict | None:
    if not settings.ESKIZ_ENABLED:
        logger.info("Eskiz SMS o‘chirilgan. Raqam: %s", phone)
        return None

    if not settings.ESKIZ_EMAIL or not settings.ESKIZ_PASSWORD:
        raise EskizError("Eskiz login ma’lumotlari kiritilmagan.")

    token = get_token()
    response = _send(phone, message, token)

    if response.status_code == 401:
        cache.delete(TOKEN_CACHE_KEY)
        token = get_token(force_refresh=True)
        response = _send(phone, message, token)

    try:
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise EskizError(
            f"SMS yuborilmadi. Eskiz status: {response.status_code}"
        ) from exc