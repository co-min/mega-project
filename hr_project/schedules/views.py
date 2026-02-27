from datetime import date
from django.contrib.auth.decorators import login_required
from .models import Schedule, DayWorkPlan

# monthly 스케줄 생성
def generate_monthly_schedule(store, year, month, employee=None):
  for day in range(1,32):
    try: 
      current_date = date (year, month, day)
    except ValueError:
      break

    weekday= current_date.weekday()

    schedules = Schedule.objects.filter(
      employee__store=store,
      work_day= weekday,
      is_active = True,
      employee__is_active = True,
      employee__created_at__lte=current_date
    ).exclude( # 퇴사일 이후 생성 X
      employee__resign_at__lt=current_date
    )
    
    if employee:
      schedules = schedules.filter(employee=employee)

    for s in schedules:
      start_time, end_time = s.start_time, s.end_time
      DayWorkPlan.objects.get_or_create(
        employee= s.employee,
        work_date = current_date,
        defaults={
          'planned_start':start_time,
          'planned_end': end_time,
          'schedule' : s,
        }
      )