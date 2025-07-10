from django.db import models
from django.contrib.auth.models import User

class LeaveRequest(models.Model):
    STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    leave_type = models.ForeignKey('core.LeaveType', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.employee.username} | {self.status}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10,choices=STATUS_CHOICES)
    marked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} | {self.date} | {self.status}"


class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)

    def __str__(self):
        return self.name


class LeaveLog(models.Model):
    leave = models.ForeignKey('LeaveRequest', on_delete=models.CASCADE)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    previous_status = models.CharField(max_length=10)
    new_status = models.CharField(max_length=10)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.leave.employee.username} | {self.previous_status} ➝ {self.new_status}"
class LeaveType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    annual_limit = models.PositiveIntegerField(default=12)

    def __str__(self):
        return self.name
class LeaveBalance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    remaining = models.PositiveIntegerField()

    class Meta:
        unique_together = ('user', 'leave_type')

    def __str__(self):
        return f"{self.user.username} - {self.leave_type.name}: {self.remaining}"    