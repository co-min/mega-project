from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime, date, time
from employees.models import Employee
from .models import AttendanceRecord


def attendance_view(request):
    """출퇴근 현황 페이지"""
    # 오늘 날짜의 출퇴근 기록
    today = date.today()
    now = datetime.now()
    current_time = now.time()
    
    # 필터링 옵션 (날짜, 부서, 상태 등)
    filter_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
    
    # 해당 날짜의 출퇴근 기록
    attendance_records = AttendanceRecord.objects.filter(
        date=filter_date
    ).select_related('employee', 'employee__department', 'employee__shift').order_by('employee__full_name')
    
    # 정렬 함수 정의
    def sort_employee_key(emp):
        shift_name = emp.shift.name if emp.shift else ''
        # 요일 그룹 정렬 (0: 월화수, 1: 목금, 2: 토일)
        day_order = 0 if '월화수' in shift_name else (1 if '목금' in shift_name else 2)
        # 시간대 정렬 (0: 오픈, 1: 미들, 2: 마감)
        time_order = 0 if '오픈' in shift_name else (1 if '미들' in shift_name else 2)
        return (day_order, time_order)
    
    # 해당 날짜에 근무 예정인 직원들만 표시
    filter_weekday = filter_date_obj.weekday()  # 0=월, 6=일
    scheduled_employees = []
    
    for emp in Employee.objects.select_related('department', 'shift').all():
        if emp.shift:
            shift_name = emp.shift.name
            # 요일 매칭 확인
            if filter_weekday in [0, 1, 2] and '월화수' in shift_name:  # 월화수
                scheduled_employees.append(emp)
            elif filter_weekday in [3, 4] and '목금' in shift_name:  # 목금
                scheduled_employees.append(emp)
            elif filter_weekday in [5, 6] and '토일' in shift_name:  # 토일
                scheduled_employees.append(emp)
    
    # 정렬: 요일 -> 시간대
    scheduled_employees.sort(key=sort_employee_key)
    
    # 기록이 있는 직원 ID 목록
    recorded_employee_ids = set(attendance_records.values_list('employee_id', flat=True))
    
    # 기록이 없는 직원에게 기본 레코드 생성
    records_list = list(attendance_records)
    for employee in scheduled_employees:
        if employee.id not in recorded_employee_ids:
            # 근무 시간이 지났는지 확인
            status = 'not_checked_in'  # 기본값: 미출근
            
            # 오늘 날짜이고 근무 시간이 설정되어 있다면
            if filter_date_obj == today and employee.shift and employee.shift.time_range:
                try:
                    time_parts = employee.shift.time_range.split('-')
                    end_time_str = time_parts[1].strip()
                    end_hour, end_minute = map(int, end_time_str.split(':'))
                    shift_end_time = time(end_hour, end_minute)
                    
                    # 근무 시간이 지났다면 결근
                    if current_time > shift_end_time:
                        status = 'absent'
                except:
                    pass
            
            # 기본 레코드 생성 (DB에 저장하지 않음)
            records_list.append(AttendanceRecord(
                employee=employee,
                date=filter_date,
                status=status
            ))
    
    # 최종 리스트 정렬: 요일 -> 시간대
    def sort_record_key(record):
        shift_name = record.employee.shift.name if record.employee.shift else ''
        # 요일 그룹 정렬 (0: 월화수, 1: 목금, 2: 토일)
        day_order = 0 if '월화수' in shift_name else (1 if '목금' in shift_name else 2)
        # 시간대 정렬 (0: 오픈, 1: 미들, 2: 마감)
        time_order = 0 if '오픈' in shift_name else (1 if '미들' in shift_name else 2)
        return (day_order, time_order)
    
    records_list.sort(key=sort_record_key)
    
    context = {
        'attendance_records': records_list,
        'filter_date': filter_date,
        'today': today,
    }
    
    return render(request, 'attendance.html', context)


def attendance_checkin_view(request):
    """출근 체크인"""
    if request.method == 'POST':
        pin = request.POST.get('pin')
        
        try:
            employee = Employee.objects.get(attendance_pin=pin)
            today = date.today()
            
            # 오늘 날짜의 기록이 있는지 확인
            record, created = AttendanceRecord.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'check_in': datetime.now().time(),
                    'status': 'working'
                }
            )
            
            if not created:
                # 이미 체크인한 경우
                messages.warning(request, f'{employee.full_name}님 이미 출근 처리되었습니다.')
            else:
                messages.success(request, f'{employee.full_name}님 출근 처리되었습니다.')
        
        except Employee.DoesNotExist:
            messages.error(request, 'PIN이 올바르지 않습니다.')
        except Exception as e:
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    
    return render(request, 'attendance_checkin.html')


def attendance_checkout_view(request):
    """퇴근 체크아웃"""
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        pin = request.POST.get('pin')
        
        try:
            employee = Employee.objects.get(pk=employee_id, attendance_pin=pin)
            today = date.today()
            
            record = AttendanceRecord.objects.get(employee=employee, date=today)
            record.check_out = datetime.now().time()
            record.status = 'finished'
            record.save()
            
            messages.success(request, f'{employee.full_name}님 퇴근 처리되었습니다.')
        
        except Employee.DoesNotExist:
            messages.error(request, '직원 정보 또는 PIN이 올바르지 않습니다.')
        except AttendanceRecord.DoesNotExist:
            messages.error(request, '출근 기록이 없습니다.')
        except Exception as e:
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    
    return redirect('attendance')
