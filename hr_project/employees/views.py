from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from datetime import date
from .models import Employee
from schedules.models import Schedule
from schedules.constants import WEEKDAYS, WORK_TIME, WORK_TYPE
from wages.models import Wage

# 직원 목록 페이지
def employees_list_view(request):
    employees = Employee.objects.filter(is_active=True)
    context = {
        'employees': employees,
    }
    return render(request, 'employee/employees.html', context)

# 직원 생성 및 수정
def employee_form_view(request, pk=None):
    employee = None
    if pk:
        employee = get_object_or_404(Employee, pk=pk)
    else:
        employee = None
    
    if request.method == 'POST':
        # 직원 데이터 수집 (form)
        full_name = request.POST.get('full_name')
        work_type = request.POST.get('work_type')
        work_day = request.POST.getlist('work_day')
        work_time = request.POST.get('work_time')
        attendance_pin = request.POST.get('attendance_pin')
        color_tag = request.POST.get('color_tag')

        # 중복된 PIN 처리
        if Employee.objects.filter(attendance_pin=attendance_pin).exclude(pk=employee.pk if employee else None).exists():
            messages.error(request, '이미 사용중인 PIN입니다.')
            return redirect(request.path)
        
        try:
            with transaction.atomic():
                # 직원 수정
                if employee:
                    Schedule.objects.filter(employee= employee).delete()
                    employee.full_name = full_name
                    employee.attendance_pin = attendance_pin
                    employee.color_tag = color_tag
                    employee.save()
                    messages.success(request, f'{full_name} 직원 정보가 수정되었습니다.')
                # 직원 생성
                else:
                    employee = Employee.objects.create(
                        full_name=full_name,
                        attendance_pin=attendance_pin,
                        color_tag=color_tag,
                    )
                    #기본 월급 생성
                    if not Wage.objects.filter(employee=employee).exists():
                        Wage.objects.create(
                            employee= employee,
                            hourly_wage = 10500,
                            effective_start_date = date.today(),
                        )
                    messages.success(request, f'{full_name} 직원이 등록되었습니다.')
            
                # 근무 유형 / 근무 타임
                if work_time and work_day and work_type:
                    for day in work_day:
                        Schedule.objects.create(
                            employee = employee,
                            work_day = int(day),
                            defaults={
                                'work_type': work_type,
                                'work_time': work_time,
                            }
                        )
        
        except Exception as e:
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    
    context = {
        'employee' : employee,
        'WEEKDAYS': WEEKDAYS,
        'WORK_TYPE' : WORK_TYPE,
        'WORK_TIME' : WORK_TIME,
    }
    return render(request, 'employee/employee_form.html', context ) 

# 직원 퇴사 처리
def employee_delete_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = False
    employee.save()
    messages.success(request, f'{employee.full_name} 직원이 퇴사 처리되었습니다.')
    
    return redirect('employees:list')