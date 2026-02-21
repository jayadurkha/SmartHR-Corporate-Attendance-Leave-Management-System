from django.db.models import Count
from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import json

from .models import Employee, Department, Attendance, LeaveRequest
from django.contrib import messages



# ==============================
# DASHBOARD
# ==============================
@login_required
def dashboard(request):

    user = request.user
    role = None

    if user.groups.filter(name='Admin').exists():
        role = "Admin"
    elif user.groups.filter(name='HR').exists():
        role = "HR"
    elif user.groups.filter(name='Viewer').exists():
        role = "Viewer"

            # ==============================
    # EMPLOYEE LEAVE STATUS
    # ==============================
    leave_requests = None

    if hasattr(user, "employee_profile"):
        leave_requests = LeaveRequest.objects.filter(
            employee=user.employee_profile
        ).order_by("-created_at")

    # DATE FILTER
    selected_date = request.GET.get("date")

    if selected_date:
        try:
            filter_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except:
            filter_date = date.today()
    else:
        filter_date = date.today()

    # TOTAL COUNTS
    total_employees = Employee.objects.count()
    total_departments = Department.objects.count()

    # TODAY STATUS COUNTS
    present_count = Attendance.objects.filter(date=filter_date, status="Present").count()
    absent_count = Attendance.objects.filter(date=filter_date, status="Absent").count()
    late_count = Attendance.objects.filter(date=filter_date, status="Late").count()

    # PERCENTAGES
    if total_employees > 0:
        present_percent = round((present_count / total_employees) * 100, 1)
        absent_percent = round((absent_count / total_employees) * 100, 1)
        late_percent = round((late_count / total_employees) * 100, 1)
    else:
        present_percent = 0
        absent_percent = 0
        late_percent = 0

    # AI MESSAGE
    if present_percent >= 80:
        ai_message = "Attendance is excellent today 👍"
    elif present_percent >= 60:
        ai_message = "Attendance is moderate today 🙂"
    else:
        ai_message = "High absenteeism detected ⚠ Please review attendance."

    dept_absent = Attendance.objects.filter(
        date=filter_date, status="Absent"
    ).values("employee__department__name").annotate(
        total=Count("id")
    ).order_by("-total").first()

    if dept_absent and dept_absent["total"] > 0:
        ai_message += f" | Most absences from {dept_absent['employee__department__name']} department."

    # ATTENDANCE TABLE
    attendance_records = Attendance.objects.filter(
        date=filter_date
    ).select_related("employee", "employee__department")

    # 30 DAY TREND
    today = timezone.now().date()
    last_30_days = [today - timedelta(days=i) for i in range(29, -1, -1)]

    labels = []
    present_data = []
    absent_data = []
    late_data = []

    for day in last_30_days:
        labels.append(day.strftime("%d %b"))
        present_data.append(
            Attendance.objects.filter(date=day, status="Present").count()
        )
        absent_data.append(
            Attendance.objects.filter(date=day, status="Absent").count()
        )
        late_data.append(
            Attendance.objects.filter(date=day, status="Late").count()
        )

    context = {
        "leave_requests": leave_requests,
        "role": role,
        "username": user.username,

        "ai_message": ai_message,

        "total_employees": total_employees,
        "total_departments": total_departments,

        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,

        "present_percent": present_percent,
        "absent_percent": absent_percent,
        "late_percent": late_percent,

        "attendance_records": attendance_records,
        "selected_date": filter_date,

        "labels": json.dumps(labels),
        "present_data": json.dumps(present_data),
        "absent_data": json.dumps(absent_data),
        "late_data": json.dumps(late_data),
    }

    return render(request, "dashboard.html", context)


# ==============================
# LEAVE REQUEST (Viewer Only)
# ==============================
@login_required
def leave_request(request):

    if not hasattr(request.user, "employee_profile"):
     return redirect("dashboard")

    if request.method == "POST":
        reason = request.POST.get("reason")
        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")

        try:
            employee = request.user.employee_profile
        except:
            messages.error(request, "Employee profile not linked to this user.")
            return redirect("dashboard")

        LeaveRequest.objects.create(
            employee=employee,
            reason=reason,
            from_date=from_date,
            to_date=to_date
        )

        messages.success(request, "Leave request sent successfully ✅")
        return redirect("dashboard")

    return render(request, "registration/leave_form.html")



# ==============================
# MANAGE LEAVES (Admin + HR)
# ==============================
@login_required
def manage_leaves(request):

    if not (
        request.user.groups.filter(name='Admin').exists() or
        request.user.groups.filter(name='HR').exists()
    ):
        return redirect("dashboard")

    leaves = LeaveRequest.objects.all().order_by("-created_at")

    return render(request, "registration/manage_leaves.html", {"leaves": leaves})




@login_required
def update_leave_status(request, leave_id, action):

    # Only Admin or HR can update
    if not (
        request.user.groups.filter(name='Admin').exists() or
        request.user.groups.filter(name='HR').exists()
    ):
        return redirect("dashboard")

    leave = LeaveRequest.objects.get(id=leave_id)

    if action == "approve":
        leave.status = "Approved"
    elif action == "reject":
        leave.status = "Rejected"

    leave.save()

    return redirect("manage_leaves")

