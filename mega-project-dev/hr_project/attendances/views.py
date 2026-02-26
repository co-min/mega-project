from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
from employees.models import Employee
from .models import AttendanceRecord
from .models import Status

# 일일 출퇴근 현황 관리용
@login_required
def attendance_view(request):
    store = request.user.store
    today = date.today()
    filter_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()

    attendance_records = AttendanceRecord.objects.filter(
        date=filter_date_obj,
        employee__store = store,
    ).select_related('employee')

    records = []
    
    for record in attendance_records:
        records.append({
            'employee': record.employee,
            'record': record,
            'check_in': record.check_in,
            'check_out': record.check_out,
            'status': record.status,
            'breaktime': record.breaktime,
        })

    context = {
        'records': records,
        'filter_date': filter_date_obj,
        'today': today,
        'breaktime_choices': [30, 60],
    }

    return render(request, "attendance/attendance_page.html", context)

# 출퇴근 기록 (POS)
@login_required
def attendance_checkin_and_out_view(request):
    store = request.user.store
    if request.method == 'POST':
        pin = request.POST.get('pin')
        today = date.today()
        now_time = datetime.now().time()
        try:
            employee = Employee.objects.get(
                attendance_pin=pin, 
                is_active=True,
                store = store
            )
            record = AttendanceRecord.objects.filter(
                employee=employee,
                date=today,
            ).first()
            # 출근 처리
            if not record:
                AttendanceRecord.objects.create(
                    employee=employee,
                    date = today,
                    check_in=now_time,
                    status = Status.WORKING,
                )
                messages.success(request, f'{employee.full_name}님 출근 처리되었습니다.')
            # 퇴근 처리
            elif record.check_in and not record.check_out:
                record.check_out = now_time
                record.status = Status.FINISHED
                record.save()
                messages.success(request, f'{employee.full_name}님 퇴근 처리되었습니다.')
            else:
                messages.error(request, f'{employee.full_name}님 이미 퇴근 처리 되었습니다.')
        
        except Employee.DoesNotExist:
            messages.error(request, 'PIN이 올바르지 않습니다.')
        except Exception as e:
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    return render(request, 'attendance/attendance_checkin.html')

# 관리자 -> 출퇴근 시간 직접 수정
@login_required
def admin_update_attendance_view(request):
    store = request.user.store
    if request.method=='POST':
        attendance_id = request.POST.get("attendance_id")
        new_check_in = request.POST.get('new_check_in')
        new_check_out = request.POST.get('new_check_out')
        record = get_object_or_404(AttendanceRecord, id=attendance_id, employee__store = store)
    
        record.check_in = datetime.strptime(new_check_in, "%H:%M").time()
        record.check_out = datetime.strptime(new_check_out, "%H:%M").time()
        record.status = Status.FINISHED

        messages.success(request, f'{record.employee.full_name}님의 근무 시간이 수정되었습니다.')
        record.save()
    
        return redirect('attendances:attendances')
    return redirect('attendances:attendances')

# 휴게시간 추가
@login_required
def add_break_time_view(request):
    store = request.user.store
    employee_id = request.POST.get('employee_id')
    date_str = request.POST.get('date')
    break_time = request.POST.get('breaktime')

    if break_time :
        breaktime = int (break_time)
    else:
        breaktime = 0
     
    employee = Employee.objects.get(pk=employee_id, store=store)
    work_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    attendance, created = AttendanceRecord.objects.get_or_create(
        employee=employee,
        date = work_date,
        defaults={
            'status': Status.WORKING,
        }
    )
    if not attendance or not attendance.check_in:
        messages.error(request, "출근 기록이 없어서 휴게시간을 설정할 수 없습니다.")
        return redirect(f'/attendances/?date={date_str}')
    
    if not attendance.check_out:
        messages.error(request, "퇴근 기록이 없어서 휴게시간을 설정할 수 없습니다.")
        return redirect(f'/attendances/?date={date_str}')
    
    dt_in = datetime.combine(work_date, attendance.check_in)
    dt_out = datetime.combine(work_date, attendance.check_out)
    worked_seconds = (dt_out - dt_in).total_seconds()
    if breaktime * 60 >= worked_seconds:
        messages.error(request, "휴게시간이 근무시간보다 길 수 없습니다.")
        return redirect(f'/attendances/?date={date_str}')

    attendance.breaktime = breaktime
    attendance.save()
    messages.success(request, "휴게시간이 적용되었습니다.")

    return redirect(f'/attendances/?date={date_str}')