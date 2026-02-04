from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime, date, timedelta
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
  work_time_map = defaultdict(timedelta)
  for record in attendance_records:
    if record.check_in and record.check_out:
      day_work = record.check_out - record.check_in
      work_time_map[record.employee] += day_work

  # 월급 계산
  salary_list = []
  for employee, total_time in work_time_map.items():
    wage = employee.wages.filter(
      effective_start_date__lte=end_date
    ).order_by('-effective_start_date').first()

    total_hour = total_time.total_seconds()/600
    monthly_salary = total_hour * wage.hourly_wage
    salary_list.append({
      'total_hour':round(total_hour, 1), # 15.5시간 등으로 표시
      'hourly_wage' : wage.hourly_wage,
      'monthly_salary' : monthly_salary,
    }
    )

  context={
      'employee' : employee,
      'year' : year,
      'month' : month,
      'salary_list' : salary_list,
    }
  return render(request, 'wage.html', context)

# 시급 수정
def change_hourly_wage_view(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    today = date.today()
    filter_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()

    year = filter_date_obj.year
    month = filter_date_obj.month
    # 변경한 시급이 적용될 날짜 (변경한 날짜의 해당 월 부터)
    adj_start_date = date(year, month, 1)

    if request.method == 'POST':
      new_hourly_wage = request.POST.get('new_hourly_wage')
      Wage.objects.create(
        employee=employee,
        hourly_wage = new_hourly_wage,
        effective_start_date=adj_start_date,
      )
      messages.success(request, f"{employee.full_name}님의 시급이 변경되었습니다.")
      return redirect ('monthly_change')


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

  total_time = timedelta()
  for record in attendance_records:
    if record.check_in and record.check_out:
      day_work = record.check_out - record.check_in
      total_time += day_work

  wage = employee.wages.filter(
      effective_start_date__lte=end_date
    ).first()
  
  total_min = total_time.total_seconds()/60
  check_salary = total_min * wage.hourly_wage/60

  context={
      'employee' : employee,
      'check_salary' : check_salary,
    }
  
  return render(request, 'calendar.html', context)
