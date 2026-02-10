from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from datetime import datetime, date
from collections import defaultdict
import calendar
from attendances.models import AttendanceRecord, Status
from employees.models import Employee
from wages.models import Wage

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

      if record.employee.is_breaktime:
        if diff_seconds>=(480*60): # 8시간 이상
          diff_seconds -= (60*60)
        elif diff_seconds>=(240*60): # 4시간 이상
          diff_seconds -= (30*60)
        
      work_second_map[record.employee]+=diff_seconds

  # 월급 계산
  salary_list = []
  for employee, total_time in work_second_map.items():
    wage = employee.wages.filter(
      effective_start_date__lte=end_date
    ).order_by('-effective_start_date').first()

    total_hour = total_time/3600
    monthly_salary = total_hour * wage.hourly_wage
    salary_list.append({
      'employee':employee,
      'total_hour':round(total_hour, 1),
      'hourly_wage' : wage.hourly_wage,
      'monthly_salary' : monthly_salary,
    }
    )
  context={
      'year' : year,
      'month' : month,
      'salary_list' : salary_list,
      'wage_choices':[10500,11000,11500,12000],
    }
  return render(request, 'wage/wages.html', context)

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
        Wage.objects.filter(employee=employee).delete()
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
  # 프론트에서 employee 선택
  employee_id = request.GET.get('employee_id')

  if not employee_id:
    return render(request, 'calendar.html')
  
  employee= get_object_or_404(Employee, id=employee_id)

  today = date.today()
  year = today.year
  month = today.month

  start_date = date(year, month, 1)
  end_date = today
  
  attendance_records = AttendanceRecord.objects.filter(
    employee= employee,
    date__range=(start_date, end_date),
    status = Status.FINISHED,
  )

  total_time = 0

  for record in attendance_records:
    if record.check_in and record.check_out:
      dt_in = datetime.combine(record.date, record.check_in)
      dt_out = datetime.combine(record.date, record.check_out)
      diff_seconds=(dt_out - dt_in).total_seconds()

      if employee.is_breaktime:
        if diff_seconds>=(480*60):
          day_work = diff_seconds -(60*60)
        elif diff_seconds>=(240*60): 
          day_work = diff_seconds - (30*60)
        else:
          day_work=diff_seconds
      else:
        day_work = diff_seconds
      total_time += day_work

  wage = employee.wages.filter(
      effective_start_date__lte=end_date
    ).order_by('-effective_start_date').first()
  
  total_hour = total_time/3600
  check_salary = total_hour * wage.hourly_wage

  context={
      'employee' : employee,
      'check_salary' : int(check_salary),
    }
  
  return render(request, 'calendar.html', context)
