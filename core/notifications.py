from django.core.mail import send_mail
from django.conf import settings
from .models import NotificationLog


def log_notification(recipient, channel, subject, message, status='SENT'):
    NotificationLog.objects.create(
        recipient=recipient,
        channel=channel,
        subject=subject,
        message=message,
        status=status,
    )


def send_email_notification(to_email, subject, message):
    if not to_email:
        return
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=True,
    )
    log_notification(recipient=to_email, channel='email', subject=subject, message=message)


def send_sms_notification(phone_number, message):
    subject = "SMS Notification"
    log_notification(recipient=phone_number, channel='sms', subject=subject, message=message)
