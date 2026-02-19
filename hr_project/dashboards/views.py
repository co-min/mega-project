from django.shortcuts import render, get_object_or_404
from datetime import date
import calendar
from attendances.services import get_monthly_attendance_calendar
from employees.models import Employee

def dashboard_view(request):
    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month
        
    employee_id = request.GET.get('employee_id')

    target_employee = None
    daily_data_map = {}

    if employee_id:
        target_employee = get_object_or_404(Employee, pk=employee_id)
        daily_data_map = get_monthly_attendance_calendar(
            year, month, target_employee
        )
    else:
        daily_data_map = {}
    
    cal_structure = calendar.monthcalendar(year, month)
    
    calendar_matrix = []
    for week in cal_structure:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'schedules': None})
            else:
                week_data.append({'day': day, 'schedules': daily_data_map.get(day)})
        calendar_matrix.append(week_data)

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
        
    employees = Employee.objects.filter(is_active=True).order_by('full_name')

    context = {
        'today': today,
        'year': year,
        'month': month,
        'calendar_matrix': calendar_matrix,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'target_employee': target_employee, 
        'employees': employees,
    }

    return render(request, 'dashboard/dashboard.html', context)