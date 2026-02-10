from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime, date
from attendances.services import get_daily_attendance_status
from employees.models import Employee
from .models import AttendanceRecord
from .models import Status

# 일일 출퇴근 현황 관리용
def attendance_view(request):
    today = date.today()
    filter_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()

    today_work_list = get_daily_attendance_status(filter_date_obj)

    context = {
        'records': today_work_list,
        'filter_date': filter_date,
        'today': today,
    }
    return render(request, "attendance/attendance_page.html", context)

"""POS에서 출/퇴근 찍었을 때, 처리하는 로직 (PIN 입력 화면)"""
# 출퇴근 기록
def attendance_checkin_and_out_view(request):
    if request.method == 'POST':
        pin = request.POST.get('pin')
        today = date.today()
        now_time = datetime.now().time()
        try:
            employee = Employee.objects.get(
                attendance_pin=pin, 
                is_active=True
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


"""출퇴근 수정 로직 (todaywork 페이지)"""
# 선택한 연/월/일의 근무기록을 불러오는 함수 (조회)
def day_attendance_view(request):
    today = date.today()
    filter_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
    
    attendance_records = AttendanceRecord.objects.filter(
        date=filter_date_obj
    ).select_related('employee')

    # 근무자의 id, (check_in, check_out)
    attendance_list = []
    for record in attendance_records:
        attendance_list.append(
            {
            'employee': record.employee,
            'attendance_id': record.id,
            'check_in': record.check_in,
            'check_out': record.check_out,
            }
        )
    context ={
        'attendance_list' : attendance_list,
    }
    return render(request, 'attendance/attendance_page.html', context)

# 관리자 -> 출퇴근 시간 직접 수정
def admin_update_attendance_view(request,attendance_id):
    record = get_object_or_404(AttendanceRecord, id=attendance_id)
    if request.method=='POST':
        new_check_in = request.POST.get('new_check_in')
        new_check_out = request.POST.get('new_check_out')
    
        record.check_in = datetime.strptime(new_check_in, "%H:%M").time()
        record.check_out = datetime.strptime(new_check_out, "%H:%M").time()
        record.status = Status.FINISHED

        messages.success(request, f'{record.employee.full_name}님의 근무 시간이 수정되었습니다.')
        record.save()

    return redirect('attendance:daywork') + f'?date={record.date}'