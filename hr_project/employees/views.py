from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from datetime import date
from .models import Employee
from schedules.models import Schedule, DayWorkPlan
from schedules.constants import WEEKDAYS, WORK_TIME, WORK_TYPE
from wages.models import Wage
from schedules.views import generate_monthly_schedule

# 직원 목록 페이지
@login_required
def employees_list_view(request):
    store = request.user.store

    if not hasattr(request.user, 'store'):
        messages.error(request, "등록된 매장이 없습니다. 매장 정보를 먼저 등록해주세요.")
        return redirect('accounts:profile')
    employees = Employee.objects.filter(
        store=store,
        is_active=True
        )
    context = {
        'employees': employees,
    }
    return render(request, 'employee/employees.html', context)

# 직원 스케줄 정보 저장
def save_employee_schedule(employee, work_type, work_day, work_time):
    # 기존 스케줄 삭제
    Schedule.objects.filter(
        employee=employee
        ).delete()
    
    for day in work_day:
        Schedule.objects.create(
            employee=employee,
            work_day=int(day),
            work_type=work_type,
            work_time=work_time,
        )

# 직원 생성
@login_required
def create_employee_form_view(request):
    store = request.user.store
    # 직원 데이터 수집 (form)
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        work_type = request.POST.get('work_type')
        work_day = request.POST.getlist('work_day')
        work_time = request.POST.get('work_time')
        attendance_pin = request.POST.get('attendance_pin')
        color_tag = request.POST.get('color_tag')

        # 중복된 PIN 처리
        if Employee.objects.filter(
            attendance_pin=attendance_pin,
            store=request.user.store
            ).exists():
            messages.error(request, '이미 사용중인 PIN입니다.')
            return redirect(request.path)
        try:
            with transaction.atomic():
                # 직원 생성
                employee = Employee.objects.create(
                    store=store,
                    full_name=full_name,
                    attendance_pin=attendance_pin,
                    color_tag=color_tag,
                    created_at = date.today()
                )
                # 직원 스케줄 저장
                save_employee_schedule(employee, work_type, work_day, work_time)
            
                # 기본 월급 생성
                Wage.objects.create(
                    employee= employee,
                    hourly_wage = 10500,
                    effective_start_date = date.today(),
                )
                today=date.today()
                generate_monthly_schedule(store, today.year, today.month, employee)
                messages.success(request, f'{full_name} 직원이 등록되었습니다.')
                return redirect('employees:list')

        except Exception as e:
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    
    context = {
        'employee' : None,
        'WEEKDAYS': WEEKDAYS,
        'WORK_TYPE' : WORK_TYPE,
        'WORK_TIME' : WORK_TIME,
    }
    return render(request, 'employee/employee_form.html', context ) 

# 직원 수정
@login_required
def edit_employee_form_view(request, pk):
    store=request.user.store
    employee = get_object_or_404(Employee, pk=pk, store = store)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        work_type = request.POST.get('work_type')
        work_day = request.POST.getlist('work_day')
        work_time = request.POST.get('work_time')
        attendance_pin = request.POST.get('attendance_pin')
        color_tag = request.POST.get('color_tag')

        # 중복된 PIN 처리
        if Employee.objects.filter(
            attendance_pin=attendance_pin,
            store=request.user.store
            ).exclude(pk=pk).exists():
            messages.error(request, '이미 사용중인 PIN입니다.')
            return redirect(request.path)
        try:
            with transaction.atomic():
                # 직원 수정
                employee.full_name = full_name
                employee.attendance_pin = attendance_pin
                employee.color_tag = color_tag
                employee.save()
                # 직원 스케줄 변경
                save_employee_schedule(employee, work_type, work_day, work_time)

                today= date.today()
                DayWorkPlan.objects.filter(
                    employee=employee,
                    work_date__gte=today,
                ).delete()
                generate_monthly_schedule(store,today.year, today.month, employee)
                messages.success(request, f'{full_name} 직원의 정보가 수정되었습니다.')
                return redirect('employees:list')
        except Exception as e:
            messages.error(request, f'오류가 발생했습니다; {str(e)}')
        
    context = {
        'employee' : employee,
        'WEEKDAYS': WEEKDAYS,
        'WORK_TYPE' : WORK_TYPE,
        'WORK_TIME' : WORK_TIME,
    }
    return render(request, 'employee/employee_form.html', context ) 
        
# 직원 퇴사 처리
@login_required
def employee_delete_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk, store=request.user.store)
    employee.is_active = False
    employee.save()
    messages.success(request, f'{employee.full_name} 직원이 퇴사 처리되었습니다.')
    
    return redirect('employees:list')