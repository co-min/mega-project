from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
import calendar
from employees.models import Employee
from wages.models import Wage
from wages.services import get_weekly_holiday_map, calculate_monthly_salary
from attendances.services import get_monthly_attendance_calendar

@login_required
def monthly_wage_view(request):
    store = request.user.store
    today = date.today()
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
            "total_hours": salary_data["total_hours"],
            "total_hour": salary_data["total_hour"],
            "total_minute": salary_data["total_minute"],
            "hourly_wage": salary_data["hourly_wage"],
            "before_tax": salary_data["before_tax"],
        })

    context = {
        "year": year,
        "month": month,
        "salary_list": salary_list,
    }

    return render(request, "wage/wages.html", context)

@login_required
# 시급 수정
def change_hourly_wage_view(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id,store = request.user.store)
    today = date.today()

    filter_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()

    year = filter_date_obj.year
    month = filter_date_obj.month
    
    if request.method == 'POST':
      new_hourly_wage = request.POST.get('new_hourly_wage')
      # 변경한 시급이 적용될 날짜 (변경한 날짜의 해당 월 부터)
      adj_start_date = date(year, month, 1)
      if new_hourly_wage:
        Wage.objects.update_or_create(
          employee=employee,
          effective_start_date=adj_start_date,
          defaults={
              'hourly_wage' : int(new_hourly_wage),
          }
        )
        messages.success(request, f"{employee.full_name}님의 시급이 변경되었습니다.")
        
      return redirect(f"{reverse('wages:wages')}?date={filter_date}")
    return redirect(f"{reverse('wages:wages')}?date={filter_date}")
  
@login_required
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