from django.shortcuts import render, get_object_or_404
from datetime import date
from .models import Schedule, DayWorkPlan
from schedule.constants import TIME_MAP
from employees.models import Employee
from attendances.models import AttendanceRecord

# monthly 스케줄 생성
def create_monthly_schedule(year, month):
  for day in range(1,32):
    try: 
      current_date = date (year, month, day)
    except ValueError:
      break

    weekday= current_date.weekday()

    schedules = Schedule.objects.filter(
      work_day= weekday,
      is_active = True,
      employee__is_active = True
    ).exclude( # 입사일 이후 생성
      employee__created_at__gt=current_date
    ).exclude( # 퇴사일 이후 생성 X
      employee__resign_at__lt=current_date
    )

    for s in schedules:
      start_time, end_time = TIME_MAP[s.work_time]
      DayWorkPlan.objects.get_or_create(
        employee= s.employee,
        work_date = current_date,
        # defaults -> create 될 때만 쓰는 값들 !
        defaults={
          'planned_start':start_time,
          'planned_end': end_time,
          'schedule' : s,
        }
      )

# 해당 날짜 (year, month, day)에 스케줄 입력
def schedule_calendar_view(request, employee_id):
  today=date.today()
  view_year = int(request.GET.get('year', today.year))
  view_month = int(request.GET.get('month', today.month))

  employee = get_object_or_404(Employee, pk=employee_id)

  work_plans = DayWorkPlan.objects.filter(
    employee = employee,
    work_date__year = view_year,
    work_date__month = view_month
  )

  attendance_records = AttendanceRecord.objects.filter(
        employee=employee,
        date__year=view_year, 
        date__month=view_month
  )

  calendar_data={}

  for plan in work_plans:
    day = plan.work_date.day
    if day not in calendar_data:
      calendar_data[day] = {'plan': None, 'record': None}
    calendar_data[day]['plan'] = plan

  for record in attendance_records:
    day = record.date.day
    if day not in calendar_data:
      calendar_data[day] = {'plan': None, 'record': None}
    calendar_data[day]['record'] = record

  context={
    'employee' : employee,
    'calendar_data' : calendar_data,
    'view_year' : view_year,
    'view_month' : view_month
  }
  return render(request, 'calendar.html', context)
