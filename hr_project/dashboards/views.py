from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, timedelta, time
import calendar
from .models import Event
from employees.models import Employee
from attendances.models import AttendanceRecord
from schedule.models import Schedule

def dashboard_view(request):
    # POST 요청 처리 - 이벤트 추가
    if request.method == 'POST' and request.POST.get('action') == 'add_event':
        today = datetime.now().date()
        # 각 직원에 대한 이벤트 처리
        for key, value in request.POST.items():
            if key.startswith('event_'):
                try:
                    employee_id = int(key.split('_')[1])
                    employee = Employee.objects.get(id=employee_id)
                    
                    # 빈 값이면 이벤트 삭제
                    if not value:
                        Event.objects.filter(employee=employee, date=today).delete()
                        # 조퇴나 병가, 휴가 상태였다면 출석 상태도 초기화
                        AttendanceRecord.objects.filter(
                            employee=employee,
                            date=today,
                            status__in=['sick_leave', 'vacation']
                        ).delete()
                        continue
                    
                    # 이벤트 이름 설정
                    event_names = {
                        'vacation': '휴가',
                        'sick_leave': '병가',
                        'substitute': '대타',
                        'early_leave': '조퇴'
                    }
                    event_name = f"{employee.full_name} - {event_names.get(value, value)}"
                    
                    # 색상 설정
                    color_map = {
                        'vacation': 'blue',
                        'sick_leave': 'purple',
                        'substitute': 'green',
                        'early_leave': 'yellow'
                    }
                    color = color_map.get(value, 'blue')
                    
                    # 이벤트 생성 또는 업데이트
                    Event.objects.update_or_create(
                        employee=employee,
                        date=today,
                        defaults={
                            'name': event_name,
                            'color': color
                        }
                    )
                    
                    # 출석 상태 업데이트
                    if value == 'sick_leave':
                        AttendanceRecord.objects.update_or_create(
                            employee=employee,
                            date=today,
                            defaults={'status': 'sick_leave'}
                        )
                    elif value == 'vacation':
                        AttendanceRecord.objects.update_or_create(
                            employee=employee,
                            date=today,
                            defaults={'status': 'vacation'}
                        )
                    elif value == 'early_leave':
                        # 조퇴는 출석 상태는 유지하되 이벤트만 생성
                        pass
                        
                except Exception as e:
                    messages.error(request, f'오류가 발생했습니다: {str(e)}')
                    continue
        
        messages.success(request, '일정이 추가되었습니다.')
        return redirect('dashboard')
    
    # URL 파라미터에서 년월 가져오기
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    today = datetime.now().date()
    
    # 이전/다음 월 계산
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    
    # 캘린더 데이터 생성
    cal = calendar.monthcalendar(year, month)
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    
    # 해당 월의 이벤트 가져오기
    events_in_month = Event.objects.filter(
        date__year=year,
        date__month=month
    ).select_related('employee')
    
    # 날짜별 이벤트 매핑
    events_by_day = {}
    attendance_records = AttendanceRecord.objects.get()
    plan = Schedule.objects.get()
    for event in events_in_month:
        day = event.date.day
        if day not in events_by_day:
            events_by_day[day] = []
        # 여기에 schedule, attendance를 이벤트로 추가해야 캘린더에서 볼 수 있는지 생각해보기 !!
        events_by_day[day].append({
            'name': event.name,
            'color': event.color,
            'employee_color': event.employee.color_tag if event.employee else '#22c55e'
        })
    
    # 해당 월의 모든 직원 가져오기
    all_employees = Employee.objects.select_related('shift').filter(shift__isnull=False)
    
    # 날짜별 직원 매핑 (요일 기반)
    employees_by_day = {}
    # 날짜별 이벤트가 있는 직원 ID 매핑
    employees_with_events_by_day = {}
    for event in events_in_month:
        day = event.date.day
        if day not in employees_with_events_by_day:
            employees_with_events_by_day[day] = set()
        if event.employee:
            employees_with_events_by_day[day].add(event.employee.id)
    
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        date_obj = datetime(year, month, day).date()
        weekday = date_obj.weekday()  # 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일
        
        employees_by_day[day] = []
        for emp in all_employees:
            # 이벤트가 있는 직원은 제외 (중복 방지)
            if emp.id in employees_with_events_by_day.get(day, set()):
                continue
                
            shift_name = emp.shift.name.lower()
            should_work = False
            
            # 월화수 (월=0, 화=1, 수=2)
            if '월화수' in shift_name and weekday in [0, 1, 2]:
                should_work = True
            # 목금 (목=3, 금=4)
            elif '목금' in shift_name and weekday in [3, 4]:
                should_work = True
            # 토일 (토=5, 일=6)
            elif '토일' in shift_name and weekday in [5, 6]:
                should_work = True
            
            if should_work:
                # 해당 날짜의 출석 기록 확인
                attendance = AttendanceRecord.objects.filter(
                    employee=emp,
                    date=date_obj
                ).first()
                
                # 출석 여부 판단
                has_checked_in = attendance and attendance.check_in is not None
                
                employees_by_day[day].append({
                    'name': emp.full_name,
                    'color_tag': emp.color_tag,
                    'time_range': emp.shift.time_range,
                    'checked_in': has_checked_in
                })
    
    # 주 단위로 날짜 정보 구성
    weeks = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'events': [], 'employees': []})
            else:
                week_data.append({
                    'day': day,
                    'events': events_by_day.get(day, []),
                    'employees': employees_by_day.get(day, [])
                })
        weeks.append(week_data)
    
    # 정렬 함수 정의
    def sort_employee_key(emp):
        shift_name = emp.shift.name if emp.shift else ''
        # 요일 그룹 정렬 (0: 월화수, 1: 목금, 2: 토일)
        day_order = 0 if '월화수' in shift_name else (1 if '목금' in shift_name else 2)
        # 시간대 정렬 (0: 오픈, 1: 미들, 2: 마감)
        time_order = 0 if '오픈' in shift_name else (1 if '미들' in shift_name else 2)
        return (day_order, time_order)
    
    # 오늘 근무 예정 직원 가져오기
    today_weekday = today.weekday()  # 0=월, 6=일
    today_working_employees = []
    
    for emp in Employee.objects.select_related('shift').all():
        if emp.shift:
            shift_name = emp.shift.name
            # 요일 매칭 확인
            if today_weekday in [0, 1, 2] and '월화수' in shift_name:  # 월화수
                today_working_employees.append(emp)
            elif today_weekday in [3, 4] and '목금' in shift_name:  # 목금
                today_working_employees.append(emp)
            elif today_weekday in [5, 6] and '토일' in shift_name:  # 토일
                today_working_employees.append(emp)
    
    # 오늘 대타 이벤트가 있는 직원도 추가 (중복 방지)
    today_substitute_events = Event.objects.filter(date=today, color='green').select_related('employee')
    today_employee_ids = {emp.id for emp in today_working_employees}
    for event in today_substitute_events:
        if event.employee and event.employee.id not in today_employee_ids and event.employee.shift:
            today_working_employees.append(event.employee)
    
    # 정렬: 요일 -> 시간대
    today_working_employees.sort(key=sort_employee_key)
    
    # 각 직원의 오늘 출석 상태 및 나이 추가
    employees_with_status = []
    for emp in today_working_employees:
        # 오늘 출석 기록 확인
        attendance = AttendanceRecord.objects.filter(
            employee=emp,
            date=today
        ).first()
        
        # 나이 계산
        age = today.year - emp.birth_year
        
        # 출석 기록이 없는 경우 근무 시간 확인하여 상태 결정
        status_display = '미출근'
        status_badge = 'gray'
        
        if attendance:
            status_display = attendance.get_status_display()
            if attendance.status == 'working':
                status_badge = 'green'
            elif attendance.status == 'finished':
                status_badge = 'orange'
            elif attendance.status == 'sick_leave':
                status_badge = 'purple'
            elif attendance.status == 'absent':
                status_badge = 'red'
            elif attendance.status == 'not_checked_in':
                status_badge = 'gray'
            else:
                status_badge = 'gray'
        else:
            # 출석 기록이 없는 경우 - 근무 시간이 지났는지 확인
            if emp.shift and emp.shift.time_range:
                try:
                    from datetime import time as time_class
                    time_parts = emp.shift.time_range.split('-')
                    end_time_str = time_parts[1].strip()
                    end_hour, end_minute = map(int, end_time_str.split(':'))
                    shift_end_time = time_class(end_hour, end_minute)
                    
                    current_time = datetime.now().time()
                    if current_time > shift_end_time:
                        status_display = '결근'
                        status_badge = 'red'
                except:
                    pass
        
        employees_with_status.append({
            'employee': emp,
            'age': age,
            'attendance': attendance,
            'status_display': status_display,
            'status_badge': status_badge
        })
    
    # 공지사항 (오늘/내일 이벤트)
    upcoming_events = Event.objects.filter(
        date__gte=today,
        date__lte=today + timedelta(days=1)
    ).select_related('employee').order_by('date', 'start')[:5]
    
    # 오늘 근무 예정 직원 목록 (모달용)
    weekday = today.weekday()  # 0=월요일, 6=일요일
    today_employees = []
    other_employees = []  # 오늘 근무가 아닌 직원들 (대타 가능)
    
    # 오늘의 이벤트 매핑 (employee_id -> event)
    today_events_map = {}
    for event in Event.objects.filter(date=today).select_related('employee'):
        if event.employee:
            today_events_map[event.employee.id] = event
    
    for emp in Employee.objects.select_related('shift').all():
        if emp.shift:
            shift_name = emp.shift.name
            is_working_today = False
            
            # 요일 매칭
            if weekday in [0, 1, 2] and '월화수' in shift_name:  # 월화수
                today_employees.append(emp)
                is_working_today = True
            elif weekday in [3, 4] and '목금' in shift_name:  # 목금
                today_employees.append(emp)
                is_working_today = True
            elif weekday in [5, 6] and '토일' in shift_name:  # 토일
                today_employees.append(emp)
                is_working_today = True
            
            # 오늘 근무가 아닌 직원은 other_employees에 추가
            if not is_working_today:
                other_employees.append(emp)
    
    context = {
        'year': year,
        'month': month,
        'month_name': month_names[month],
        'today': today,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'weekdays': weekdays,
        'weeks': weeks,
        'employees_with_status': employees_with_status,
        'upcoming_events': upcoming_events,
        'today_employees': today_employees,
        'other_employees': other_employees,
        'today_events_map': today_events_map,
    }
    
    return render(request, 'dashboard.html', context)
