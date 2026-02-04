from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, date
from employees.models import Employee
from .models import AttendanceRecord
from .models import Status
from schedule.models import DayWorkPlan

# 출퇴근 현황 페이지
def attendance_view(request):
    # 해당 날짜
    today = date.today()
    filter_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
    
    # 예정된 근무
    work_plans = DayWorkPlan.objects.filter(
        work_date = filter_date_obj
    ).select_related('employee').order_by('employee__full_name')

    # 실제 출퇴근 기록
    attendance_records = AttendanceRecord.objects.filter(
        date=filter_date_obj
    ).select_related('employee')

    attendance_map = {r.employee_id: r for r in attendance_records} # 출퇴근 기록이 있는 직원
    plan_map = {p.employee_id: p for p in work_plans} # 출퇴근이 예정된 직원
    
    all_employee_ids = set(attendance_map.keys()) | set(plan_map.keys()) # 모든 직원 (for 대타 처리)

    employees = Employee.objects.filter(
        id__in=all_employee_ids
    ).order_by('full_name')

    records_list = []

    for emp in employees:
        record = attendance_map.get(emp.id)
        plan = plan_map.get(emp.id)
        # 대타 (계획 X, 기록 O)
        is_substitute = (plan is None and record is not None)

        # 출근 기록이 있는 경우
        if record:
            # 상태 결정
            if record.check_out:
                new_status = Status.FINISHED
                ui_status = 'FINISHED'
            else:
                new_status = Status.WORKING
                ui_status = 'WORKING'

            if record.status != new_status:
                record.status = new_status
                record.save()

        # 출근 기록이 없는 경우
        else:
            if filter_date_obj < today:
                ui_status = 'ABSENT' # 결근
            else:
                ui_status = 'PLANNED' # 출근 전

        # 리스트 추가
        records_list.append({
            'employee': emp,
            'record': record,
            'plan' : plan,
            'ui_status': ui_status,
            'is_substitute': is_substitute
        })

    # 실제 출근한 시간 순 + 출근하지 않은 사람은 맨 뒤로
    records_list.sort(
        key=lambda x: (
            x['record'].check_in 
            if x['record'] and x['record'].check_in 
            else datetime.max.time()
    ))

    context = {
        'records': records_list,
        'filter_date': filter_date,
        'today': today,
    }
    return render(request, 'calendar.html', context)


# 관리자 -> 출퇴근 시간 직접 수정
def admin_update_attendance(attendance_id, new_check_in, new_check_out):
    attendance_record = AttendanceRecord.objects.get(
        id = attendance_id
    )

    if(new_check_in>new_check_out):
        messages.error('...')
    
    attendance_record.check_in = new_check_in
    attendance_record.check_out = new_check_out
    messages.success('근무 시간이 업데이트 되었습니다.')
    
    attendance_record.save()
    return attendance_record
    

# 출근 체크인
def attendance_checkin_view(request):
    if request.method == 'POST':
        pin = request.POST.get('pin')
        try:
            employee = Employee.objects.get(attendance_pin=pin, is_active=True)
            today = date.today()
            now_time = datetime.now().time()

            # 오늘 날짜의 기록이 있는지 확인
            record, created = AttendanceRecord.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'check_in': now_time,
                    'status': Status.WORKING
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

# 퇴근 체크아웃
def attendance_checkout_view(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        pin = request.POST.get('pin')
        
        try:
            employee = Employee.objects.get(pk=employee_id, attendance_pin=pin, is_active = True)
            today = date.today()
            now_time=datetime.now().time()
            
            record = AttendanceRecord.objects.get(
                employee=employee,
                date=today
            )
            
            if record.check_out is not None:
                # 이미 체크아웃한 경우
                messages.warning(request, f'{employee.full_name}님 이미 퇴근 처리되었습니다.')
            else:
                record.check_out = now_time
                record.status = Status.FINISHED
                record.save()
                messages.success(request, f'{employee.full_name}님 퇴근 처리되었습니다.')
        
        except Employee.DoesNotExist:
            messages.error(request, '직원 정보 또는 PIN이 올바르지 않습니다.')
        except AttendanceRecord.DoesNotExist:
            messages.error(request, '출근 기록이 없습니다.')
        except Exception as e:
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    
    return redirect('attendance')