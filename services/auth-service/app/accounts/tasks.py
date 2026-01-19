from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_otp_email(email, otp):
    send_mail(
        subject="Your OTP",
        message=f"Your OTP is {otp}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5)
def send_otp_email_task(self, email, otp):
    send_mail(
        subject="Your Login OTP",
        message=f"Your OTP is {otp}",
        from_email=None,
        recipient_list=[email],
    )