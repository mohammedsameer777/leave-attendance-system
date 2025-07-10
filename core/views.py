from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import LeaveRequest, Attendance, LeaveLog, Holiday,LeaveType
from .forms import LeaveForm ,ManualAttendanceForm
from django.http import HttpResponse
from .signals import set_current_user
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.contrib import messages
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from datetime import date
import weasyprint
from django.contrib.auth import logout
from django.shortcuts import redirect
# -------------------- Employee Views --------------------
@login_required
def apply_leave(request):
    form = LeaveForm(request.POST or None)
    leave_types = LeaveType.objects.all()

    if request.method == "POST":
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = request.user

            # Manually assign leave_type from POST
            leave_type_id = request.POST.get("leave_type")
            if leave_type_id:
                try:
                    leave.leave_type = LeaveType.objects.get(id=leave_type_id)
                except LeaveType.DoesNotExist:
                    messages.error(request, "Invalid leave type selected.")
                    return render(request, 'core/apply_leave.html', {
                        'form': form,
                        'leave_types': leave_types
                    })
            else:
                messages.error(request, "Please select a leave type.")
                return render(request, 'core/apply_leave.html', {
                    'form': form,
                    'leave_types': leave_types
                })

            leave.save()
            messages.success(request, "Leave applied successfully!")
            return redirect('leave_history')
        else:
            messages.error(request, "There was a problem with your form.")
            print(form.errors)

    return render(request, 'core/apply_leave.html', {
        'form': form,
        'leave_types': leave_types
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

    already_marked = Attendance.objects.filter(employee=request.user, date=today).exists()
    if not already_marked:
        Attendance.objects.create(employee=request.user, date=today, present=True)
        messages.success(request, "Attendance marked successfully.")
    else:
        messages.info(request, "Attendance already marked for today.")

    return redirect('attendance_history')


@login_required
def attendance_history(request):
    attendance = Attendance.objects.filter(employee=request.user).order_by('-date')
    return render(request, 'core/attendance_history.html', {'attendance': attendance})


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


def attendance_summary(request):
    selected_date = request.GET.get('date', timezone.localdate().isoformat())
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()

    all_users = User.objects.all()
    attendance_records = Attendance.objects.filter(date=selected_date)

    present_users = [a.user for a in attendance_records if a.status == 'Present']
    absent_users = [u for u in all_users if u not in present_users]

    is_holiday = Holiday.objects.filter(date=selected_date).exists()

    return render(request, 'core/attendance_summary.html', context= {
        'selected_date': selected_date,
        'present_users': present_users,
        'absent_users': absent_users,
        'is_holiday': is_holiday
    })
def manual_attendance_entry(request):
    if request.method == 'POST':
        form = ManualAttendanceForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['date']
            if Holiday.objects.filter(date=selected_date).exists():
                messages.error(request, "Cannot mark attendance on a holiday.")
            else:
                form.save()
                messages.success(request, "Attendance marked successfully.")
                return redirect('manual_attendance')
    else:
        form = ManualAttendanceForm()
    return render(request, 'core/manual_attendance.html', {'form': form})
def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST.get('role')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            if role == 'admin' and user.is_staff:
                return redirect('/admin/')  # Go to admin panel
            elif role == 'employee' and not user.is_staff:
                return redirect('/apply/')  # Go to employee dashboard
            else:
                return render(request, 'registration/login.html', {'error': 'Access denied for selected role'})
        else:
            return render(request, 'registration/login.html', {'error': 'Invalid credentials'})

    return render(request, 'registration/login.html')
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
    response['Content-Disposition'] = f'attachment; filename="Leave_Requests.pdf"'
    return response
def export_holiday_pdf(request):
    holidays = Holiday.objects.all()
    html_string = render_to_string('core/admin_export_pdf.html', {'queryset': holidays, 'title': 'Holidays'})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=holidays.pdf'

    weasyprint.HTML(string=html_string).write_pdf(response)
    return response
def logout_view(request):
    logout(request)
    return redirect('login') 