from datetime import datetime, date, timedelta
import calendar
from attendances.models import AttendanceRecord, Status

DEFAULT_WAGE = 10500
"""
# 주휴수당 계산
# (1주일 소정 근로 시간/40) * 8시간 * 시급
# 조건 1: 일주일에 15시간 이상 근로
# 조건 2: 일주일 동안의 소정 근로일에 모두 출근 (지각 조퇴 상관 X)
# 조건 3: 다음주 출근 예정(퇴사 예정자에게는 지급하지 않음)
"""
# 주휴 포함 월급 계산
def calculate_weekly_holiday_allowance(employee, start, end):
    total_allowance = 0
    # 시작일 : 월요일
    week_start = start - timedelta(days=start.weekday())
    while week_start <=end:
      week_end = week_start+timedelta(days=6)
      if week_end > end:
         break
      attendance_records = AttendanceRecord.objects.filter(
          employee=employee,
          employee__store=employee.store,
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
          ).order_by('-effective_start_date', '-id').first()
        hourly_wage = wage.hourly_wage if wage else DEFAULT_WAGE
        total_allowance += holiday_work_hours * hourly_wage
      week_start += timedelta(days=7)

    return total_allowance

# 일주일 마다 발생한 주휴 계산
def get_weekly_holiday_map(employee, start, end):
  holiday_map ={}
  # 월요일
  week_start = start - timedelta(days=start.weekday())

  while week_start <=end:
    week_end = week_start + timedelta(days=6)
    sunday = week_end
    attendance_records = AttendanceRecord.objects.filter(
        employee=employee,
        employee__store=employee.store,
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
        diff = max(diff, 0)
        total_seconds += diff
    total_hours = total_seconds /3600

    # 주휴 조건 만족 
    if total_hours >= 15:
      holiday_work_hours = (min(total_hours, 40) / 40) * 8
      wage = employee.wages.filter(
            effective_start_date__lte=week_end
        ).order_by('-effective_start_date', '-id').first()
      
      hourly_wage = wage.hourly_wage if wage else DEFAULT_WAGE
      allowance = holiday_work_hours * hourly_wage

      # 일요일이 이번달 안에 있는 경우에만 추가
      if start <= sunday <= end:
        holiday_map[sunday] = allowance
    week_start += timedelta(days=7)
  return holiday_map

def calculate_monthly_salary(employee, year, month):
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    attendance_records = AttendanceRecord.objects.filter(
        employee=employee,
        employee__store=employee.store,
        date__range=(start_date, end_date),
        status=Status.FINISHED,
        check_out__isnull=False
    )

    total_seconds = 0

    for record in attendance_records:
        dt_in = datetime.combine(record.date, record.check_in)
        dt_out = datetime.combine(record.date, record.check_out)
        diff = (dt_out - dt_in).total_seconds()

        if record.breaktime:
            diff -= record.breaktime * 60

        total_seconds += max(diff, 0)

    total_hours = total_seconds / 3600
    total_hour = int(total_seconds // 3600)
    total_minute = int((total_seconds % 3600) // 60)

    wage_obj = employee.wages.filter(
        effective_start_date__lte=end_date
    ).order_by('-effective_start_date', '-id').first()

    hourly_wage = wage_obj.hourly_wage if wage_obj else DEFAULT_WAGE
    weekly_bonus = calculate_weekly_holiday_allowance(employee, start_date, end_date)
    total_salary = (total_hours * hourly_wage) + weekly_bonus

    return {
        "total_hours": total_hours,
        "total_hour" : total_hour,
        "total_minute" : total_minute,
        "hourly_wage": hourly_wage,
        "weekly_bonus": int(weekly_bonus),
        "before_tax": int(total_salary),
        "after_tax": int(total_salary * 0.967),
    }