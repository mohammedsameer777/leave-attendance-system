from django import forms
from .models import LeaveRequest,Attendance
from django.contrib.auth.models import User
from django.utils import timezone

class LeaveForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'end_date', 'reason']

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date < timezone.localdate():
            raise forms.ValidationError("Cannot apply for leave in the past.")
        return start_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date.")
class ManualAttendanceForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label="Employee")
    date = forms.DateField(widget=forms.SelectDateWidget)
    status = forms.ChoiceField(choices=Attendance.STATUS_CHOICES)

    class Meta:
        model = Attendance
        fields = ['user', 'date', 'status']