from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
import calendar
from employees.models import Employee
from wages.services import get_weekly_holiday_map, calculate_monthly_salary
from attendances.services import get_monthly_attendance_calendar
from accounts.decorators import store_required
import csv
from django.http import HttpResponse
from attendances.models import AttendanceRecord, Status

@login_required
@store_required
def monthly_wage_view(request):
    store = request.user.store
    today = date.today()
    date_param = request.GET.get('date')
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d')
            year = selected_date.year
            month = selected_date.month
        except ValueError:
            year, month = today.year, today.month
    else:
        try:
            year = int(request.GET.get('year', today.year))
            month = int(request.GET.get('month', today.month))
        except ValueError:
            year, month = today.year, today.month

    employees = Employee.objects.filter(
        is_active=True,
        store=store
        )

    salary_list = []

    for employee in employees:
        salary_data = calculate_monthly_salary(employee, year, month)

        salary_list.append({
            "employee": employee,
            "year":year,
            "month":month,
            "total_hours": salary_data["total_hours"],
            "total_hour": salary_data["total_hour"],
            "total_minute": salary_data["total_minute"],
            "hourly_wage": salary_data["hourly_wage"],
            "before_tax": salary_data["before_tax"],
            "after_tax":salary_data["after_tax"],
            "weekly_bonus" : salary_data["weekly_bonus"]
        })

    context = {
        "year": year,
        "month": month,
        "salary_list": salary_list,
    }

    return render(request, "wage/wages.html", context)

@login_required
@store_required
# 직원 개인 캘린더
def check_wage_view(request):
    employee_id = request.GET.get('employee_id')
    if not employee_id:
        return render(request, 'calendar/calendar.html', {'error': '직원 정보가 없습니다.'})

    employee = get_object_or_404(Employee, id=employee_id, store=request.user.store )
    today = date.today()
    
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month
    
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    holiday_map = get_weekly_holiday_map(employee, start_date, end_date)
    daily_data_map = get_monthly_attendance_calendar(year, month, employee)

    total_hours = 0
    for day_data in daily_data_map.values():
        if day_data and day_data.get('work_hours'):
            total_hours += day_data['work_hours']
            
    hours = int(total_hours)
    minutes = int((total_hours - hours) * 60)
    total_hours_str = f"{hours}시간 {minutes}분"

    _, last_day = calendar.monthrange(year, month)
    end_date = date(year, month, last_day)
    
    salary_data = calculate_monthly_salary(employee, year, month)
    estimated_salary = salary_data ["before_tax"]

    cal_structure = calendar.monthcalendar(year, month)
    calendar_matrix = []
    
    for week in cal_structure:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'attendance': None})
            else:
                current_date = date(year, month, day)
                week_data.append({
                    'day': day, 
                    'attendance': daily_data_map.get(day),
                    'holiday_allowance' : holiday_map.get(current_date)
                })
        calendar_matrix.append(week_data)

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
        
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    context = {
        'employee': employee,
        'year': year, 'month': month,
        'calendar_matrix': calendar_matrix,
        'total_hours_str': total_hours_str,
        'estimated_salary': estimated_salary,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
    }
    
    return render(request, 'calendar/calendar.html', context)

# 급여 파일 다운로드
@login_required
@store_required
def export_monthly_wage_csv(request):
    store = request.user.store
    
    try:
        year = int(request.GET.get("year", 2026))
        month = int(request.GET.get("month", 3))
    except (ValueError, TypeError):
        return HttpResponse("잘못된 날짜 형식입니다.", status=400)

    employees = Employee.objects.filter(store=store, is_active=True)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig') # utf-8-sig로 한글 깨짐 방지
    response['Content-Disposition'] = f'attachment; filename="mega_wage_{year}_{month}.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "직원명",
        "총 근무시간",
        "주휴수당",
        "시급",
        "총 급여(세전)"
        "총 급여(세후)"
    ])

    for emp in employees:
        salary_data = calculate_monthly_salary(emp, year, month)

        work_days = AttendanceRecord.objects.filter(
            employee=emp,
            date__year=year,
            date__month=month,
            status=Status.FINISHED
        ).count()

        weekly_allowance = salary_data.get("weekly_allowance", 0)

        writer.writerow([
            emp.full_name,
            f"{salary_data['total_hours']}시간",
            salary_data["weekly_bonus"],
            salary_data["hourly_wage"],
            salary_data["before_tax"],
            salary_data["after_tax"],
        ])

    return response
