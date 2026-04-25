import logging
from datetime import datetime
from html import escape

from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def _display_name(user):
    return escape((user.first_name or user.username or "Coder").strip())


def _avatar_url(user):
    profile = getattr(user, "profile", None)
    avatar = getattr(profile, "avatar", None) if profile else None
    if not avatar:
        return ""
    try:
        url = avatar.url
    except Exception:
        return ""

    if url.startswith("http://") or url.startswith("https://"):
        return url

    base_url = settings.BACKEND_URL.rstrip("/")
    return f"{base_url}{url}"


def _otp_email_html(otp):
    safe_otp = escape(str(otp))
    year = datetime.now().year
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login Code - CLASHCODE</title>
  <style>
    @media only screen and (max-width: 600px) {{
      .wrapper {{ padding: 20px !important; }}
      .card {{ padding: 32px 20px !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#0f172a;font-family:'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;-webkit-font-smoothing:antialiased;">
  <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding: 40px 10px;" class="wrapper">
        <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="max-width:480px;background-color:#1e293b;border:1px solid #334155;border-radius:16px;overflow:hidden;" class="card">
          <tr>
            <td align="center" style="padding: 40px 24px 12px;">
              <div style="font-size:20px;font-weight:800;letter-spacing:3px;color:#f8fafc;text-transform:uppercase;">CLASH OF <span style="color:#fbbf24;">CODE</span></div>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 24px 24px;">
              <div style="height:1px;width:40px;background-color:#334155;"></div>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 32px 10px;">
              <div style="font-size:16px;color:#94a3b8;line-height:1.5;">Your one-time login verification code</div>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:24px 32px;">
              <div style="display:inline-block;padding:20px 32px;background-color:#0f172a;border:1px solid #334155;border-radius:12px;">
                <span style="font-size:36px;font-weight:800;letter-spacing:6px;color:#fbbf24;line-height:1;">{safe_otp}</span>
              </div>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:8px 32px 40px;">
              <p style="margin:0;font-size:14px;color:#64748b;line-height:1.6;">
                This code expires in 10 minutes.<br>
                If you didn't request this code, you can safely ignore this email.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:24px;background-color:#1a2333;border-top:1px solid #334155;text-align:center;">
              <p style="margin:0;font-size:12px;color:#64748b;letter-spacing:0.5px;">&copy; {year} CLASHCODE. All rights reserved.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _welcome_email_html(user):
    name = _display_name(user)
    avatar = _avatar_url(user)
    year = datetime.now().year

    avatar_block = (
        f'<img src="{escape(avatar)}" alt="Avatar" width="88" height="88" '
        'style="display:block;width:88px;height:88px;border-radius:50%;object-fit:cover;border:3px solid #334155;box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">'
        if avatar
        else f'<div style="width:88px;height:88px;border-radius:50%;background-color:#334155;color:#f8fafc;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:700;border:3px solid #475569;">{name[:1]}</div>'
    )

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome - CLASHCODE</title>
</head>
<body style="margin:0;padding:0;background-color:#0f172a;font-family:'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;-webkit-font-smoothing:antialiased;">
  <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding: 40px 10px;">
        <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="max-width:520px;background-color:#1e293b;border:1px solid #334155;border-radius:16px;overflow:hidden;">
          <tr>
            <td align="center" style="padding: 44px 32px 16px;">
              <div style="font-size:18px;font-weight:800;letter-spacing:3px;color:#f8fafc;text-transform:uppercase;">CLASH OF <span style="color:#fbbf24;">CODE</span></div>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding: 12px 32px 24px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="padding: 12px; background-color:#1e293b; border-radius: 50%;">
                    {avatar_block}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 40px 12px;">
              <h1 style="margin:0;font-size:26px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px;">Welcome to the clan, <span style="color:#fbbf24;">{name}</span></h1>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 44px 44px;">
              <p style="margin:0;font-size:16px;color:#94a3b8;line-height:1.6;">
                Your account is officially ready. It's time to test your skills, solve challenges, and climb the leaderboard.
              </p>
              <div style="margin-top:32px;">
                <a href="{settings.FRONTEND_URL}" style="display:inline-block;padding:14px 32px;background-color:#fbbf24;color:#0f172a;font-weight:700;text-decoration:none;border-radius:10px;font-size:15px;box-shadow:0 4px 6px -1px rgba(251, 191, 36, 0.2);">Start Your First Challenge</a>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:24px;background-color:#1a2333;border-top:1px solid #334155;text-align:center;">
              <p style="margin:0;font-size:12px;color:#64748b;letter-spacing:0.5px;">&copy; {year} CLASHCODE. All rights reserved.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def send_welcome_email(user):
    """
    Send a minimal welcome email to a newly registered user.
    """
    subject = "Welcome to CLASHCODE"

    try:
        html_message = _welcome_email_html(user)

        plain_message = (
            f"Welcome to CLASHCODE.\n\n"
            f"Hi {user.first_name or user.username},\n\n"
            "Your account is ready.\n"
            "Start with your first challenge.\n\n"
            "— CLASHCODE"
        )

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info("Welcome email sent to %s", user.email)

    except Exception:
        logger.exception("Failed to send welcome email to %s", user.email)


def send_otp_email(email, otp):
    """
    Send an OTP email for login verification.
    """
    subject = "Your Login Code - CLASHCODE"

    try:
        html_message = _otp_email_html(otp)

        plain_message = (
            f"Your CLASHCODE login code is {otp}.\n\n"
            "This code expires in 10 minutes.\n"
            "If you didn’t request this, ignore this email."
        )

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info("OTP email sent to %s", email)
        return True

    except Exception:
        logger.exception("Failed to send OTP email to %s", email)
        return False
