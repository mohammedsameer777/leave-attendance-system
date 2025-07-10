from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import LeaveRequest, LeaveLog
from threading import local

# Thread-local to store user in request
_user = local()

def set_current_user(user):
    _user.value = user

def get_current_user():
    return getattr(_user, 'value', None)

@receiver(pre_save, sender=LeaveRequest)
def log_leave_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # It's a new leave, not an update

    try:
        old = LeaveRequest.objects.get(pk=instance.pk)
    except LeaveRequest.DoesNotExist:
        return

    if old.status != instance.status:
        LeaveLog.objects.create(
            leave=instance,
            previous_status=old.status,
            new_status=instance.status,
            changed_by=get_current_user()
        )
