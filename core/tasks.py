from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import Holiday
from django.utils import timezone

@shared_task
def send_attendance_reminder():
    today = timezone.localdate()
    
    # Check if today is a holiday
    if Holiday.objects.filter(date=today).exists():
        return 'Skipped – Today is a holiday'

    # Get all admin users
    admins = User.objects.filter(is_staff=True, is_superuser=True)
    
    for admin in admins:
        send_mail(
            subject='Attendance Reminder',
            message='Please mark the attendance for today.',
            from_email='admin@company.com',
            recipient_list=[admin.email],
            fail_silently=False,
        )
    return f"Sent to {admins.count()} admins"