from django.contrib import admin
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import io
from django.db.models import F

from .models import LeaveRequest, Holiday, LeaveLog, Attendance, LeaveType,LeaveBalance

# --------------------- Custom Admin Actions ---------------------

@admin.action(description='Approve selected leave requests')
def approve_leaves(modeladmin, request, queryset):
    for leave in queryset:
        if leave.status != 'APPROVED':
            # 👇 Optional: reduce leave balance
            try:
                LeaveBalance.objects.filter(
                    employee=leave.employee,
                    leave_type=leave.leave_type
                ).update(
                    balance=F('balance') - (leave.end_date - leave.start_date).days + 1
                )
            except LeaveBalance.DoesNotExist:
                pass  # or handle it if needed

            # 👇 Log and approve
            LeaveLog.objects.create(
                leave=leave,
                changed_by=request.user,
                previous_status=leave.status,
                new_status='APPROVED'
            )
            leave.status = 'APPROVED'
            leave.save()

# ✅ Reject action
@admin.action(description='Reject selected leave requests')
def reject_leaves(modeladmin, request, queryset):
    for leave in queryset:
        if leave.status != 'REJECTED':
            LeaveLog.objects.create(
                leave=leave,
                changed_by=request.user,
                previous_status=leave.status,
                new_status='REJECTED'
            )
            leave.status = 'REJECTED'
            leave.save()
@admin.action(description='Export selected leave requests to PDF')
def export_selected_to_pdf(modeladmin, request, queryset):
    html_string = render_to_string('core/admin_export_pdf.html', {'queryset': queryset})
    html = HTML(string=html_string)

    # Generate PDF in memory
    pdf_file = io.BytesIO()
    html.write_pdf(target=pdf_file)
    pdf_file.seek(0)

    # Return as downloadable file
    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="leave_requests.pdf"'
    return response


# --------------------- Admin Models ---------------------

@admin.register(LeaveRequest)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date', 'end_date')
    actions = [approve_leaves, reject_leaves, export_selected_to_pdf]

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'status')

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')

@admin.register(LeaveLog)
class LeaveLogAdmin(admin.ModelAdmin):
    list_display = ('leave', 'changed_by', 'previous_status', 'new_status', 'changed_at')
    list_filter = ('new_status', 'changed_by', 'changed_at')

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'annual_limit')
