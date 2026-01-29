from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Employee
from wages.models import Wage
from datetime import date

#직원 목록 및 설정 페이지
def employees_list_view(request):
    employees = Employee.objects.filter(is_active=True)
    context = {
        'employees': employees,
    }
    return render(request, 'employees_list.html', context)

#직원 생성 및 수정
def employee_form_view(request, pk=None):
    employee = None
    if pk:
        employee = get_object_or_404(Employee, pk=pk)
    else:
        employee = None
    
    if request.method == 'POST':
        # 직원 데이터 수집 (form)
        full_name = request.POST.get('full_name')
        hourly_wage = request.POST.get('hourly_wage')
        attendance_pin = request.POST.get('attendance_pin')
        color_tag = request.POST.get('color_tag')

        # 중복된 PIN 처리
        if Employee.objects.filter(attendance_pin=attendance_pin):
            messages.error(request, '이미 사용중인 PIN입니다.')
            return redirect(request.path)
        
        try:
            # 직원 수정
            if employee:
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
                messages.success(request, f'{full_name} 직원이 등록되었습니다.')
            
            #시급 관리
            if hourly_wage:
                new_wage = int(hourly_wage)
                latest_wage = Wage.objects.filter(employee=employee).order_by('-effective_start_date').first()
                # 시급이 첫 입력/변경된 경우
                if not latest_wage or latest_wage.hourly_wage != new_wage:
                    Wage.objects.create(
                        employee=employee,
                        hourly_wage=int(hourly_wage),
                        effective_start_date = date.today()
                    )
            return redirect('employees')
        
        except Exception as e:
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    
    context = {
        'employee' : employee,
    }
    return render(request, 'employee_form.html', context ) 

# 직원 퇴사 처리
def employee_delete_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.is_active = False
    employee.save()
    messages.success(request, f'{employee.full_name} 직원이 퇴사 처리되었습니다.')
    
    return redirect('employees')