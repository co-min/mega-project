from datetime import date, datetime
from schedules.models import DayWorkPlan
from employees.models import Employee
from attendances.models import AttendanceRecord, Status
import calendar

# 해당 날짜의 스케줄 리스트 반환
def get_daily_attendance_status(target_date, employee):
    plan = DayWorkPlan.objects.filter(
            work_date=target_date,
            employee = employee,
        ).first()

    record = AttendanceRecord.objects.filter(
                date = target_date,
                employee=employee,
        ).first()

    today = date.today()

    # 대타 (계획 X, 기록 O)
    is_substitute = (plan is None and record is not None)
    # plan 객체가 있는 경우
    planned_start = plan.planned_start if plan else None
    planned_end = plan.planned_end if plan else None
    # record 객체가 있는 경우
    check_in = record.check_in if record else None
    check_out = record.check_out if record else None
    status = Status.PLANNED

    if record:
        # 상태 결정
        if check_out:
            status = Status.FINISHED
        else:
            status = Status.WORKING

        # 자동 퇴근 처리
        if check_in and not check_out and target_date < today:
            record.check_out = planned_end
            record.status = Status.FINISHED
            record.save()
            status = Status.FINISHED

    # 출근 기록이 없는 경우
    else:
        if target_date < today and plan:
            status = Status.ABSENT
        elif plan:
            status = Status.PLANNED
        else:   
            status = None

    # 근무시간 계산
    work_hours = 0
    break_time = getattr(record, 'breaktime', 0) if record else 0

    if check_in and check_out:
        dt_in = datetime.combine(target_date, check_in)
        dt_out = datetime.combine(target_date, check_out)
        seconds = (dt_out - dt_in).total_seconds()
        seconds -= break_time * 60
        work_hours = round(max(seconds, 0) / 3600, 1)

    return {
        'plan': plan,
        'record': record,
        'status': status,
        'planned_start': planned_start,
        'planned_end': planned_end,
        'check_in': check_in,
        'check_out': check_out,
        'is_substitute' : is_substitute,
        'work_hours': work_hours,
        'breaktime': break_time,
    }
       

# 캘린더 한 칸에 표시되는 항목 고르기
def daily_calendar_display_date(target_date, employee):
    item = get_daily_attendance_status(target_date, employee)
    status = item['status']

    if item['check_in']:
        time_text = item['check_in'].strftime('%H:%M')
        if item['check_out']:
            time_text += f" - {item['check_out'].strftime('%H:%M')}"
    elif item['planned_start'] and item['planned_end']:
        time_text = f"{item['planned_start'].strftime('%H:%M')} - {item['planned_end'].strftime('%H:%M')}"
    else:
        time_text = ""
    css_class = ''
    if status == Status.PLANNED:
        css_class = 'planned'
    elif status == Status.WORKING:
        css_class = 'working'
    elif status == Status.FINISHED:
        css_class = 'finished'
    elif status == Status.ABSENT:
        css_class = 'absent'

    return {
        'time': time_text,
        'status': status,
        'css_class': css_class,
        'is_substitute': item['is_substitute'],
        'breaktime' : item['breaktime'],
        'work_hours':item['work_hours']
    }



# 한 칸 -> 전체 캘린더로 매핑
def get_monthly_attendance_calendar(year: int, month: int, employee):
    _, last_day = calendar.monthrange(year, month)
    calendar_map = {}

    for day in range(1, last_day + 1):
        current_date = date(year, month, day)
        calendar_map[day] = daily_calendar_display_date(current_date, employee)
    return calendar_map