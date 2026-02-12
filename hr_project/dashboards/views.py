from django.shortcuts import render
from datetime import date
import calendar
from attendances.services import get_monthly_attendance_calendar
from employees.models import Employee

def dashboard_view(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    # 달력 숫자판
    cal = calendar.monthcalendar(year, month)
    # 근무 데이터
    calendar_data = get_monthly_attendance_calendar(year, month)
    employees = Employee.objects.filter(is_active=True).order_by('full_name')

    formatted_calendar=[]
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                # 날짜 없는 빈칸
                week_data.append({'day': 0, 'schedules': []})
            else:
                # 날짜 있는 칸 -> 데이터 매칭
                week_data.append({
                    'day': day,
                    'schedules': calendar_data.get(day, [])
                })
        formatted_calendar.append(week_data)

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    context = {
        'today': today,
        'year': year,
        'month': month,
        'calendar_matrix': formatted_calendar,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'employees':employees
    }

    return render(request, 'dashboard/dashboard.html', context)
