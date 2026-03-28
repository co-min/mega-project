from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from datetime import date
from .models import Employee
from schedules.models import Schedule, DayWorkPlan
from schedules.constants import WEEKDAYS, WORK_TYPE
from wages.models import Wage
from schedules.views import generate_monthly_schedule
from accounts.decorators import store_required


def get_used_color_tags(store, exclude_employee_pk=None):
    queryset = Employee.objects.filter(store=store, is_active=True)
    if exclude_employee_pk is not None:
        queryset = queryset.exclude(pk=exclude_employee_pk)
    return {color.lower() for color in queryset.values_list('color_tag', flat=True) if color}

# 직원 목록 페이지
@login_required
@store_required
def employees_list_view(request):
    store = request.user.store
    employees = Employee.objects.filter(
        store=store,
        is_active=True
        )
    context = {
        'employees': employees,
    }
    return render(request, 'employee/employees.html', context)

# 직원 스케줄 정보 저장
def save_employee_schedule(employee, work_type, work_day, start_time, end_time):
    # 기존 스케줄 삭제
    Schedule.objects.filter(
        employee=employee
        ).delete()
    
    for day in work_day:
        Schedule.objects.create(
            employee=employee,
            work_day=int(day),
            work_type=work_type,
            start_time=start_time,
            end_time = end_time,
        )

# 직원 생성
@login_required
@store_required
def create_employee_form_view(request):
    store = request.user.store
    # 직원 데이터 수집 (form)
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        work_type = request.POST.get('work_type')
        work_day = request.POST.getlist('work_day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        attendance_pin = request.POST.get('attendance_pin')
        color_tag = request.POST.get('color_tag') or '#22c55e'
        new_hourly_wage = request.POST.get('hourly_wage')

        # 중복된 PIN 처리
        if Employee.objects.filter(
            attendance_pin=attendance_pin,
            store=request.user.store
            ).exists():
            messages.error(request, '이미 사용중인 PIN입니다.')
            return redirect(request.path)

        used_color_tags = get_used_color_tags(store)
        if color_tag.lower() in used_color_tags:
            messages.error(request, '이미 다른 직원이 사용 중인 색상입니다.')
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
                save_employee_schedule(employee, work_type, work_day, start_time, end_time)
            
                # 시급 저장
                hourly_wage = int(new_hourly_wage) if new_hourly_wage else 10500
                Wage.objects.create(
                    employee=employee,
                    hourly_wage=hourly_wage,
                    effective_start_date=date.today(),
                    )
                
                today=date.today()
                generate_monthly_schedule(store, today.year, today.month, employee)
                messages.success(request, f'{full_name} 직원이 등록되었습니다.')
                return redirect('employees:list')

        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    wage_options = list(range(10500, 12500, 500))
    
    context = {
        'employee' : None,
        'WEEKDAYS': WEEKDAYS,
        'WORK_TYPE' : WORK_TYPE,
        'wage_options' : wage_options,
        'unavailable_colors': sorted(get_used_color_tags(store)),
        
    }
    return render(request, 'employee/employee_form.html', context ) 

# 직원 수정
@login_required
@store_required
def edit_employee_form_view(request, pk):
    store=request.user.store
    employee = get_object_or_404(Employee, pk=pk, store = store)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        work_type = request.POST.get('work_type')
        work_day = request.POST.getlist('work_day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        attendance_pin = request.POST.get('attendance_pin')
        color_tag = request.POST.get('color_tag') or employee.color_tag
        new_hourly_wage = request.POST.get('hourly_wage')


        # 중복된 PIN 처리
        if Employee.objects.filter(
            attendance_pin=attendance_pin,
            store=request.user.store
            ).exclude(pk=pk).exists():
            messages.error(request, '이미 사용중인 PIN입니다.')
            return redirect(request.path)

        used_color_tags = get_used_color_tags(store, exclude_employee_pk=pk)
        if color_tag.lower() in used_color_tags:
            messages.error(request, '이미 다른 직원이 사용 중인 색상입니다.')
            return redirect(request.path)

        try:
            with transaction.atomic():
                # 직원 수정
                employee.full_name = full_name
                employee.attendance_pin = attendance_pin
                employee.color_tag = color_tag
                employee.save()

                # 직원 스케줄 변경
                save_employee_schedule(employee, work_type, work_day, start_time, end_time)

                # 시급 수정
                if new_hourly_wage:
                    wage_int = int(new_hourly_wage)

                    if wage_int % 500 != 0:
                        messages.error(request, "시급은 500원 단위로만 설정 가능합니다.")
                        return redirect(request.path)

                    today = date.today()
                    effective_date = date(today.year, today.month, 1)

                    Wage.objects.update_or_create(
                        employee=employee,
                        effective_start_date=effective_date,
                        defaults={
                            'hourly_wage': wage_int,
                        }
                    )
                
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

    # 월급 선택 
    current_wage = Wage.objects.filter(
        employee=employee,
    ).order_by('-effective_start_date').first()

    wage_options = list(range(10500, 12500, 500))

    # 수정 시 form에 정보 넣기
    schedules = Schedule.objects.filter(employee=employee, is_active=True).order_by("work_day")
    first_schedule = schedules.first()

    work_day_selected = list(schedules.values_list("work_day", flat=True))

    initial_work_type = first_schedule.work_type if first_schedule else ""
    initial_start_time = first_schedule.start_time.strftime("%H:%M") if first_schedule and first_schedule.start_time else ""
    initial_end_time = first_schedule.end_time.strftime("%H:%M") if first_schedule and first_schedule.end_time else ""
        
    context = {
        'employee' : employee,
        'WEEKDAYS': WEEKDAYS,
        'WORK_TYPE' : WORK_TYPE,
        'current_wage': current_wage.hourly_wage if current_wage else 10500,
        'wage_options' : wage_options,
        'work_day_selected': work_day_selected,
        'initial_work_type': initial_work_type,
        'initial_start_time': initial_start_time,
        'initial_end_time': initial_end_time,
        'unavailable_colors': sorted(get_used_color_tags(store, exclude_employee_pk=pk)),
    }
    return render(request, 'employee/employee_form.html', context ) 
        
# 직원 퇴사 처리
@login_required
@store_required
def employee_delete_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk, store=request.user.store)
    employee.is_active = False
    employee.save()
    messages.success(request, f'{employee.full_name} 직원이 퇴사 처리되었습니다.')
    
    return redirect('employees:list')