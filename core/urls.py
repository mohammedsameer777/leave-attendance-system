from django.urls import path
from . import views
from .views import (
    leave_logs,
    manual_attendance,
    custom_login_view,
    export_holiday_pdf,
    logout_view,
)

urlpatterns = [
    # Auth
    path('login/', custom_login_view, name='login'),
    path('accounts/logout/', logout_view, name='logout'),

    # Leave
    path('apply/', views.apply_leave, name='apply_leave'),
    path('history/', views.leave_history, name='leave_history'),
    path('leaves/', views.admin_leave_list, name='admin_leave_list'),
    path('update/<int:pk>/<str:status>/', views.update_leave_status, name='update_leave_status'),
    path('leave-logs/', leave_logs, name='leave_logs'),

    # Attendance
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/history/', views.attendance_history, name='attendance_history'),
    path('attendance-summary/', views.attendance_summary, name='attendance_summary'),
    path('manual-attendance/', manual_attendance, name='manual_attendance'),

    # Exports
    path('export-attendance-pdf/', views.export_attendance_pdf, name='export_attendance_pdf'),
    path('export-leave-pdf/', views.export_leave_pdf, name='export_leave_pdf'),
    path('export/holidays/', export_holiday_pdf, name='export_holiday_pdf'),
]
