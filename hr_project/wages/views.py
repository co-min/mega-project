from django.shortcuts import render
from datetime import datetime, date, timedelta
from collections import defaultdict
import calendar
from attendances.models import AttendanceRecord
from attendances.models import Status

# 한 달 월급 계산
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
    ).first()

    total_min = total_time.total_seconds()/60
    monthy_salary = total_min * wage.hourly_wage/60
    salary_list.append({
      'employee' : employee,
      'monthy_salary' : monthy_salary,
    }
    )

  context={
      'year' : year,
      'month' : month,
      'salary_list' : salary_list,
    }
  return render(request, 'wage.html', context)

# 근무자 조회 시 월급 계산
# 조회 시 월급 ? or 한 달 월급으로 ??