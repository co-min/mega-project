from datetime import date, datetime
from schedules.models import DayWorkPlan
from employees.models import Employee
from attendances.models import AttendanceRecord, Status
import calendar

# 해당 날짜의 스케줄 리스트 반환
def get_daily_attendance_status(target_date):
    work_plans = DayWorkPlan.objects.filter(
        work_date=target_date,
    ).select_related('employee')

    attendance_records = AttendanceRecord.objects.filter(
            date = target_date
    ).select_related('employee')

    attendance_map = {r.employee_id: r for r in attendance_records} # 출퇴근 기록이 있는 직원
    plan_map = {p.employee_id: p for p in work_plans} # 출퇴근이 예정된 직원

    all_employee_ids = set(attendance_map.keys()) | set(plan_map.keys()) # 모든 직원 (for 대타 처리)

    employees = Employee.objects.filter(
        id__in=all_employee_ids
    ).order_by('full_name')

    result =[]
    today = date.today()

    for emp in employees:
        plan = plan_map.get(emp.id)
        record = attendance_map.get(emp.id)
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

            # 퇴근 안 찍고 감 -> 자동 퇴근 처리
            if check_in and not check_out and target_date < today:
                record.check_out = planned_end
                record.status = Status.FINISHED
                record.save()
                status = Status.FINISHED

        # 출근 기록이 없는 경우
        else:
            if target_date < today:
                status = Status.ABSENT
            else:
                status = Status.PLANNED

        # 결과 리스트 추가
        result.append({
            'employee': emp,
            'plan': plan,
            'record': record,
            'status': status,
            'is_substitute': is_substitute,
            'planned_start': planned_start,
            'planned_end': planned_end,
            'check_in': check_in,
            'check_out': check_out,
        })

    result.sort(
    key=lambda x: x['check_in'] if x['check_in'] else datetime.max.time()
    )
    return result

# 캘린더 한 칸에 표시되는 항목 고르기
def daily_calendar_display_date(target_date):
    today_work_list = get_daily_attendance_status(target_date)
    display_list = []
    for item in today_work_list:
        emp = item['employee']
        status = item['status']
        if item['check_in']:
            time_text = item['check_in'].strftime('%H:%M')
            if item['check_out']:
                time_text += f" - {item['check_out'].strftime('%H:%M')}"
        elif item['planned_start'] and item['planned_end']:
            time_text = f"{item['planned_start'].strftime('%H:%M')} - {item['planned_end'].strftime('%H:%M')}"
        else:
            time_text = ""
        
        if status == Status.PLANNED:
            css_class = 'planned'
        elif status == Status.WORKING:
            css_class = 'working'
        elif status == Status.FINISHED:
            css_class = 'finished'
        elif status == Status.ABSENT:
            css_class = 'absent'

        display_list.append({
            'name': emp.full_name,
            'time': time_text,
            'status': status,
            'css_class': css_class,
            'is_substitute': item['is_substitute'],
        })
    return display_list

# 한 칸 -> 전체 캘린더로 매핑
def get_monthly_attendance_calendar(year: int, month: int):
    _, last_day = calendar.monthrange(year, month)
    calendar_map = {}

    for day in range(1, last_day + 1):
        current_date = date(year, month, day)
        daily_work_calendar = daily_calendar_display_date(current_date)
        calendar_map[day] = daily_work_calendar

    return calendar_map