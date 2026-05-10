"""Notification + email service layer."""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from .models import Notification

logger = logging.getLogger(__name__)


def _safe_send(subject, body, to_email):
    """Send email and never raise. Returns True/False."""
    if not to_email:
        return False
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        logger.warning("Email send failed: %s", e)
        return False


def create_notification(user, kind, title, body='', email=False):
    n = Notification.objects.create(user=user, kind=kind, title=title, body=body)
    if email:
        ok = _safe_send(title, body, user.email)
        if ok:
            n.email_sent = True
            n.save(update_fields=['email_sent'])
    return n


def send_login_notification(user, request=None):
    ip = ''
    if request is not None:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR', '')
    body = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Your DQMS account was just signed in to.\n"
        f"IP: {ip}\n\n"
        f"If this wasn't you, please reset your password immediately.\n\n"
        f"— DQMS"
    )
    return create_notification(user, 'login', "New sign-in to your DQMS account", body, email=True)


def send_welcome_email(user, verify_token):
    verify_url = f"{settings.SITE_URL}{reverse('accounts:verify_email', args=[verify_token])}"
    body = (
        f"Welcome to DQMS, {user.first_name or user.username}!\n\n"
        f"Verify your email to activate all features:\n{verify_url}\n\n"
        f"— DQMS"
    )
    return create_notification(user, 'welcome', "Welcome to DQMS — please verify your email", body, email=True)


def notify_test_completion(user, test_name, score, passed):
    status = "passed" if passed else "needs another attempt"
    title = f"Test result: {test_name}"
    body = (
        f"Hi {user.first_name or user.username},\n\n"
        f"You scored {score}% on {test_name}. Status: {status}.\n\n"
        f"Keep going — consistency builds mastery.\n— DQMS"
    )
    return create_notification(user, 'test', title, body, email=True)


def notify_review_due(user, topic_name, review_number):
    title = f"Review #{review_number} due for {topic_name}"
    body = (
        f"Hi {user.first_name or user.username},\n\n"
        f"It's time to revise '{topic_name}' (review #{review_number}).\n"
        f"Complete it today to keep your spaced-repetition schedule on track.\n\n— DQMS"
    )
    return create_notification(user, 'review', title, body, email=True)


def notify_badge_earned(user, badge_name):
    title = f"🏆 Badge earned: {badge_name}"
    body = (
        f"Congratulations {user.first_name or user.username}!\n"
        f"You've earned the '{badge_name}' badge in DQMS.\n\n— DQMS"
    )
    return create_notification(user, 'badge', title, body, email=True)


def notify_streak(user, days):
    title = f"🔥 {days}-day streak!"
    body = f"Amazing! You've been learning for {days} days in a row. Keep the streak alive!"
    return create_notification(user, 'streak', title, body, email=False)
