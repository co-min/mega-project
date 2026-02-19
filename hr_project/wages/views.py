from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from datetime import datetime, date, timedelta
from collections import defaultdict
import calendar
from attendances.models import AttendanceRecord, Status
from employees.models import Employee
from wages.models import Wage
from attendances.services import get_monthly_attendance_calendar

"""월급 계산 및 시급 수정 (wage 페이지)"""
# 한 달 월급 계산 (조회)
def monthly_wage_view (request):
  today = date.today()
  filter_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
  filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()

  year = filter_date_obj.year
  month = filter_date_obj.month

  start_date = date(year, month, 1)
  end_date = date(year, month, calendar.monthrange(year, month)[1])

  attendance_records = AttendanceRecord.objects.filter(
    date__range=(start_date, end_date),
    status = Status.FINISHED
  ).select_related('employee')

  # 월 근무 시간 계산 및 저장
  work_second_map = defaultdict(float)
  for record in attendance_records:
    if record.check_in and record.check_out:
      dt_in = datetime.combine(record.date, record.check_in)
      dt_out = datetime.combine(record.date, record.check_out)
      diff_seconds=(dt_out - dt_in).total_seconds()
      # 휴게 시간 계산
      if record.breaktime:
        diff_seconds -= (record.breaktime *60)
        diff_seconds = max(diff_seconds, 0)
          
      work_second_map[record.employee] += diff_seconds

  employees = Employee.objects.filter(is_active=True)

  # 월급 계산
  salary_list = []
  for employee in employees:
    total_time = work_second_map.get(employee, 0)
    total_hour = int(total_time // 3600)
    total_minute = int((total_time % 3600) // 60)

    wage = employee.wages.filter(
      effective_start_date__lte=end_date,
    ).order_by('-effective_start_date').first()

    hourly_wage = wage.hourly_wage if wage else 10500

    # 주휴 수당 고려
    weekly_holiday_bonus = calculate_weekly_holiday_allowance(employee, start_date, end_date)
    salary = (total_time / 3600) * hourly_wage + weekly_holiday_bonus

    # 세전
    before_tax_monthly_salary = salary
    # 세후
    after_tax_monthly_salary = int(salary * 0.967)

    salary_list.append({
      'employee':employee,
      'total_hour': total_hour,
      'total_minute': total_minute,
      'hourly_wage' : hourly_wage,
      'weekly_holiday_bonus':int(weekly_holiday_bonus),
      'before_tax_monthly_salary' : int(before_tax_monthly_salary),
      'after_tax_monthly_salary':int(after_tax_monthly_salary),
      'effective_start_date': wage.effective_start_date if wage else None,
    }
    )
  context={
      'year' : year,
      'month' : month,
      'salary_list' : salary_list,
      'wage_choices':[10500,11000,11500,12000],
    }
  return render(request, 'wage/wages.html', context)

# 주휴수당 계산 뷰
# (1주일 소정 근로 시간/40) * 8시간 * 시급
# 조건 1: 일주일에 15시간 이상 근로
# 조건 2: 일주일 동안의 소정 근로일에 모두 출근 (지각 조퇴 상관 X)
# 조건 3: 다음주 출근 예정(퇴사 예정자에게는 지급하지 않음)
def calculate_weekly_holiday_allowance(employee, start, end):
    total_allowance=0
    # 시작일 : 월요일
    week_start = start - timedelta(days=start.weekday())
    while week_start <=end:
      week_end = min(week_start + timedelta(days=6), end)
      attendance_records = AttendanceRecord.objects.filter(
          employee=employee,
          date__range=[week_start, week_end],
          status=Status.FINISHED,
          check_out__isnull=False
      )

      total_seconds = 0

      for record in  attendance_records :
        dt_in = datetime.combine(record.date, record.check_in)
        dt_out = datetime.combine(record.date, record.check_out)
        diff = (dt_out - dt_in).total_seconds()
        if record.breaktime:
          diff -= record.breaktime * 60
          diff = max(diff,0)
        total_seconds += diff
      total_hours = total_seconds /3600
          
      # 주휴 조건 만족 
      if total_hours >= 15:
        holiday_work_hours = (min(total_hours, 40) / 40) * 8
        wage = employee.wages.filter(
              effective_start_date__lte=week_end
          ).order_by('-effective_start_date').first()
        hourly_wage = wage.hourly_wage if wage else 10500
        total_allowance += holiday_work_hours * hourly_wage
      week_start += timedelta(days=7)

    return total_allowance

# 시급 수정
def change_hourly_wage_view(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
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
        Wage.objects.create(
          employee=employee,
          hourly_wage = new_hourly_wage,
          effective_start_date=adj_start_date,
        )
        messages.success(request, f"{employee.full_name}님의 시급이 변경되었습니다.")
        
      return redirect(f"{reverse('wages:monthly')}?date={filter_date}")
    return redirect(f"{reverse('wages:monthly')}?date={filter_date}")
  

"""근무자 조회 -> 월급 표시 (캘린더)"""
# 근무자 조회 시 해당 일까지 월급 계산
def check_wage_view(request):
    print("====== daily_data_map ======")
    
    employee_id = request.GET.get('employee_id')
    if not employee_id:
        return render(request, 'calendar.html', {'error': '직원 정보가 없습니다.'})

    employee = get_object_or_404(Employee, id=employee_id)
    
    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

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
    
    wage_obj = employee.wages.filter(effective_start_date__lte=end_date).order_by('-effective_start_date').first()
    hourly_wage = wage_obj.hourly_wage if wage_obj else 10500
    
    estimated_salary = int(total_hours * hourly_wage)

    cal_structure = calendar.monthcalendar(year, month)
    calendar_matrix = []
    
    for week in cal_structure:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'attendance': None})
            else:
                week_data.append({
                    'day': day, 
                    'attendance': daily_data_map.get(day) 
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
    print(daily_data_map)


    context = {
        'employee': employee,
        'year': year, 'month': month,
        'calendar_matrix': calendar_matrix,
        'total_hours_str': total_hours_str,
        'estimated_salary': estimated_salary,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
    }
    
    return render(request, 'dashboard/dashboard.html', context)