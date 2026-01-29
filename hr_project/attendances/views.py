from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime, date
from employees.models import Employee
from .models import AttendanceRecord
from .models import Status
from schedule.models import DayWorkPlan


#출퇴근 현황 페이지
def attendance_view(request):
    # 오늘 날짜의 출퇴근 기록
    today = date.today()
    filter_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
    
    # 실제 출퇴근 기록
    attendance_records = AttendanceRecord.objects.filter(
        date=filter_date_obj
    ).select_related('employee').order_by('employee__full_name')

    records_list = list(attendance_records)
    recorded_ids = {r.employee.id for r in records_list}

    # 해당 날짜에 근무 예정인 직원들
    work_plans = DayWorkPlan.objects.filter(
        work_date = filter_date_obj
    ).select_related('employee').order_by('employee__full_name')

    # 근무 예정인 직원들이 출근하지 않았다면
    for plan in work_plans:
        if plan.employee.id not in recorded_ids:
            records_list.append(
                AttendanceRecord(
                    employee=plan.employee,
                    date = filter_date_obj,
                    status = Status.NOT_CHECKED_IN
                )
            )

    # 출퇴근 기록에 문제가 있는 경우
    if filter_date_obj < today:
        for record in records_list:
            #출근은 했지만 퇴근을 안 찍은 경우
            if record.check_in is not None and record.check_out is None:
                #check_out을 자동으로 DayWorkPlan의 end_time으로 update
                try:
                    plan = DayWorkPlan.objects.get(
                        employee = record.employee,
                        work_date=filter_date_obj
                    )
                    record.check_out = plan.end_time
                    record.status=Status.FINISHED
                    record.save()
                except DayWorkPlan.DoesNotExist:
                    record.status = Status.ABSENT

    records_list.sort(key=lambda r: r.employee.full_name)
    
    context = {
        'attendance_records': records_list,
        'filter_date': filter_date,
        'today': today,
    }
    
    return render(request, 'attendance.html', context)


#출근 체크인
def attendance_checkin_view(request):
    if request.method == 'POST':
        pin = request.POST.get('pin')
        try:
            employee = Employee.objects.get(attendance_pin=pin, is_active=True)
            today = date.today()
            now_time = datetime.now().time()

            # 오늘 날짜의 기록이 있는지 확인
            #get_or_create
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

#퇴근 체크아웃
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
