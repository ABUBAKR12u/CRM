import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

from app.model.users import User
from app.utils.config import settings

logger = logging.getLogger(__name__)

RESET_EMAIL = {
    "uz": (
        "Parolni tiklash",
        "Salom, {name}!\n\nParolni tiklash uchun havola:\n{link}\n\n"
        "Havola {minutes} daqiqa amal qiladi. Agar siz so'ramagan bo'lsangiz, xatni e'tiborsiz qoldiring.",
    ),
    "ru": (
        "Восстановление пароля",
        "Здравствуйте, {name}!\n\nСсылка для восстановления пароля:\n{link}\n\n"
        "Ссылка действует {minutes} минут. Если вы не запрашивали восстановление, проигнорируйте письмо.",
    ),
    "en": (
        "Password reset",
        "Hello, {name}!\n\nUse this link to reset your password:\n{link}\n\n"
        "The link is valid for {minutes} minutes. If you did not request it, ignore this email.",
    ),
}


def send_email(to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD.get_secret_value())
            smtp.send_message(message)
    except smtplib.SMTPException, OSError:
        logger.exception("Failed to send email to %s", to)


def send_reset_email(user: User, token: str, locale: str) -> None:
    subject, template = RESET_EMAIL[locale]
    link = f"{settings.FRONTEND_URL}/{locale}/reset-password?token={quote(token)}"
    body = template.format(name=user.name, link=link, minutes=settings.RESET_TOKEN_MINUTES)
    send_email(user.email, subject, body)
