"""
Email service — async SMTP via aiosmtplib.

Supports Gmail SMTP with App Passwords.
All emails rendered from Jinja2 HTML templates.
"""

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings

logger = logging.getLogger(__name__)

# Template engine
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=True,
)


async def _send_raw(to: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP. Returns True on success."""
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured — skipping email to %s", to)
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
            start_tls=settings.SMTP_START_TLS,
        )
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


def _render(template_name: str, **ctx: object) -> str:
    """Render an email template with context."""
    tpl = _jinja_env.get_template(template_name)
    return tpl.render(app_name=settings.APP_NAME, **ctx)


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

async def send_invite_email(
    to: str,
    company_name: str,
    invite_url: str,
    role: str = "company",
) -> bool:
    """Send an invitation email to join the platform."""
    html = _render(
        "invite.html",
        to_email=to,
        company_name=company_name,
        invite_url=invite_url,
        role=role,
    )
    return await _send_raw(to, f"You're invited to join {company_name} on {settings.APP_NAME}", html)


async def send_password_reset_email(
    to: str,
    reset_url: str,
) -> bool:
    """Send a password reset email."""
    html = _render(
        "password_reset.html",
        to_email=to,
        reset_url=reset_url,
    )
    return await _send_raw(to, f"Reset your {settings.APP_NAME} password", html)


async def send_welcome_email(
    to: str,
    name: str,
    login_url: str,
) -> bool:
    """Send a welcome email after invite acceptance."""
    html = _render(
        "welcome.html",
        to_email=to,
        name=name,
        login_url=login_url,
    )
    return await _send_raw(to, f"Welcome to {settings.APP_NAME}!", html)
