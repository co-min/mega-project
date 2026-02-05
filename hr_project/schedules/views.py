from django.shortcuts import redirect
from datetime import date
from .models import Schedule, DayWorkPlan
from schedules.constants import TIME_MAP


# monthly 스케줄 생성
def generate_monthly_schedule_view(request, year, month):
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
        defaults={
          'planned_start':start_time,
          'planned_end': end_time,
          'schedule' : s,
        }
      )

    return redirect('employees:list') 