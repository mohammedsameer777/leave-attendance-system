from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from datetime import datetime, date
from django.contrib.auth.models import User

from .models import LeaveRequest, Attendance, LeaveLog, Holiday, LeaveType
from .forms import LeaveForm, ManualAttendanceForm
from .signals import set_current_user


# -------------------- Employee Views --------------------

@login_required
def apply_leave(request):
    form = LeaveForm(request.POST or None)
    leave_types = LeaveType.objects.all()

    if request.method == "POST":
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = request.user

            leave_type_id = request.POST.get("leave_type")
            if leave_type_id:
                try:
                    leave.leave_type = LeaveType.objects.get(id=leave_type_id)
                except LeaveType.DoesNotExist:
                    messages.error(request, "Invalid leave type selected.")
                    return render(request, 'core/apply_leave.html', {
                        'form': form, 'leave_types': leave_types
                    })
            else:
                messages.error(request, "Please select a leave type.")
                return render(request, 'core/apply_leave.html', {
                    'form': form, 'leave_types': leave_types
                })

            leave.save()
            messages.success(request, "Leave applied successfully!")
            return redirect('leave_history')
        else:
            messages.error(request, "There was a problem with your form.")
            print(form.errors)

    return render(request, 'core/apply_leave.html', {
        'form': form, 'leave_types': leave_types
    })


@login_required
def leave_history(request):
    leaves = LeaveRequest.objects.filter(employee=request.user)
    return render(request, 'core/leave_history.html', {'leaves': leaves})


@login_required
def mark_attendance(request):
    today = timezone.localdate()

    if Holiday.objects.filter(date=today).exists():
        messages.warning(request, "Today is a holiday.")
        return redirect('attendance_history')

    already_marked = Attendance.objects.filter(user=request.user, date=today).exists()
    if already_marked:
        messages.info(request, "Attendance already marked for today.")
    else:
        Attendance.objects.create(user=request.user, date=today, status='PRESENT')
        messages.success(request, "Attendance marked successfully.")

    return redirect('attendance_history')


@login_required
def attendance_history(request):
    records = Attendance.objects.filter(user=request.user).order_by('-date')
    return render(request, 'core/attendance_history.html', {'records': records})


# -------------------- Admin Views --------------------

@user_passes_test(lambda u: u.is_staff)
def admin_leave_list(request):
    leaves = LeaveRequest.objects.all()
    return render(request, 'core/admin_leave_list.html', {'leaves': leaves})


@user_passes_test(lambda u: u.is_staff)
def update_leave_status(request, pk, status):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    set_current_user(request.user)
    leave.status = status
    leave.save()
    return render(request, 'core/partials/leave_status.html', {'leave': leave})


@staff_member_required
def leave_logs(request):
    logs = LeaveLog.objects.select_related('leave', 'changed_by').order_by('-changed_at')
    return render(request, 'core/logs.html', {'logs': logs})

@user_passes_test(lambda u: u.is_staff)
def manual_attendance(request):
    users = User.objects.all()
    today = timezone.localdate()

    if request.method == "POST":
        selected_user_ids = request.POST.getlist("user_ids")
        
        for user_id in selected_user_ids:
            user = User.objects.get(id=user_id)
            # Delete any duplicate existing records for today
            Attendance.objects.filter(user=user, date=today).delete()
            # Create one clean record
            Attendance.objects.create(user=user, date=today, status='PRESENT')

        messages.success(request, "Manual attendance marked successfully.")
        return redirect("attendance_summary")

    return render(request, "core/manual_attendance.html", {
        "users": users,
        "today": today,
    })


@login_required
def attendance_summary(request):
    date_str = request.GET.get("date")
    if date_str:
        date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        date = timezone.localdate()

    present_attendance = Attendance.objects.filter(date=date, status='PRESENT').select_related("user")
    present_user_ids = present_attendance.values_list('user_id', flat=True)

    all_user_ids = User.objects.values_list("id", flat=True)
    absent_users = User.objects.exclude(id__in=present_user_ids)

    return render(request, "core/attendance_summary.html", {
        "date": date,
        "present_users": present_attendance,  # these are Attendance instances
        "absent_users": absent_users,        # these are User instances
    })

@login_required
def export_attendance_pdf(request):
    today = date.today()
    records = Attendance.objects.filter(date=today)

    html_string = render_to_string('core/export_attendance_pdf.html', {
        'records': records,
        'date': today
    })
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Attendance_{today}.pdf"'
    return response


def export_leave_pdf(request):
    leaves = LeaveRequest.objects.all()
    html_string = render_to_string('core/export_leave_pdf.html', {
        'leaves': leaves,
    })
    pdf_file = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Leave_Requests.pdf"'
    return response


def export_holiday_pdf(request):
    holidays = Holiday.objects.all()
    html_string = render_to_string('core/admin_export_pdf.html', {
        'queryset': holidays,
        'title': 'Holidays'
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=holidays.pdf'
    HTML(string=html_string).write_pdf(response)
    return response


def logout_view(request):
    logout(request)
    return redirect('login')


def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("apply_leave")  # or any page
    
        else:
            messages.error(request, "Invalid credentials")
    return render(request, "registration/login.html")
