from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime, time
from .models import Employee, Department, Shift, RoleSetting, MaxSetting, HiringSlot
from attendances.models import AttendanceRecord


def auto_checkout_expired_shifts():
    """근무 시간이 지난 직원들을 자동으로 퇴근 처리"""
    now = datetime.now()
    today = now.date()
    current_time = now.time()
    
    # 오늘 근무 중인 모든 출석 기록
    working_records = AttendanceRecord.objects.filter(
        date=today,
        status='working',
        employee__shift__isnull=False
    ).select_related('employee__shift')
    
    for record in working_records:
        shift = record.employee.shift
        # time_range에서 종료 시간 추출 (예: "08:00-16:00")
        if shift and shift.time_range:
            try:
                time_parts = shift.time_range.split('-')
                if len(time_parts) == 2:
                    end_time_str = time_parts[1].strip()
                    end_hour, end_minute = map(int, end_time_str.split(':'))
                    shift_end_time = time(end_hour, end_minute)
                    
                    # 근무 종료 시간이 지났으면 자동 퇴근 처리
                    if current_time >= shift_end_time:
                        record.status = 'finished'
                        if not record.check_out:
                            record.check_out = shift_end_time
                        record.save()
            except (ValueError, IndexError):
                # time_range 파싱 실패 시 무시
                continue


def employees_list_view(request):
    """직원 목록 및 설정 페이지"""
    # 자동 퇴근 처리 실행
    auto_checkout_expired_shifts()
    
    # POST 요청 처리 (설정 업데이트)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_roles':
            # 역할 설정 업데이트
            for role in RoleSetting.objects.all():
                base_wage = request.POST.get(f'base_wage_{role.id}')
                wage_type = request.POST.get(f'wage_type_{role.id}')
                increase = request.POST.get(f'increase_{role.id}')
                
                if base_wage:
                    role.base_wage = int(base_wage)
                if wage_type:
                    role.wage_type = wage_type
                if increase:
                    role.increase_per_6_month = int(increase)
                role.save()
            messages.success(request, '역할 설정이 업데이트되었습니다.')
        
        elif action == 'update_max':
            # 최대/최소 급여 설정 업데이트
            max_wage = request.POST.get('max_wage')
            min_wage = request.POST.get('min_wage')
            
            max_setting = MaxSetting.objects.first()
            if max_setting:
                if max_wage:
                    max_setting.max_wage = int(max_wage)
                if min_wage:
                    max_setting.min_wage = int(min_wage)
                max_setting.save()
                messages.success(request, '최대/최소 급여 설정이 업데이트되었습니다.')
        
        elif action == 'update_hiring':
            # 구인 상태 업데이트
            for slot in HiringSlot.objects.all():
                status = request.POST.get(f'status_{slot.id}')
                if status:
                    slot.status = status
                    slot.save()
            
            # 새로운 구인 슬롯 추가
            counter = 1
            while True:
                new_type = request.POST.get(f'new_type_{counter}')
                new_days = request.POST.get(f'new_days_{counter}')
                new_time = request.POST.get(f'new_time_{counter}')
                new_status = request.POST.get(f'new_status_{counter}')
                
                if not new_type or not new_days or not new_time:
                    break
                
                # Shift 이름 생성
                shift_name = f'{new_type} {new_days} ({new_time})'
                
                # Shift가 존재하는지 확인, 없으면 생성
                shift, created = Shift.objects.get_or_create(
                    name=shift_name,
                    defaults={
                        'time_range': new_time,
                        'days': 'custom'
                    }
                )
                
                # HiringSlot 생성
                HiringSlot.objects.create(
                    shift=shift,
                    status=new_status if new_status else 'open'
                )
                
                counter += 1
            
            messages.success(request, '구인 상태가 업데이트되었습니다.')
        
        elif action == 'delete_hiring':
            # 구인 슬롯 삭제
            slot_id = request.POST.get('slot_id')
            if slot_id:
                try:
                    slot = HiringSlot.objects.get(id=slot_id)
                    shift_name = slot.shift.name
                    slot.delete()
                    messages.success(request, f'{shift_name} 구인 슬롯이 삭제되었습니다.')
                except HiringSlot.DoesNotExist:
                    messages.error(request, '구인 슬롯을 찾을 수 없습니다.')
        
        return redirect('employees')
    
    # 정렬 함수 정의
    def sort_employee_key(emp):
        shift_name = emp.shift.name if emp.shift else ''
        # 요일 그룹 정렬 (0: 월화수, 1: 목금, 2: 토일)
        day_order = 0 if '월화수' in shift_name else (1 if '목금' in shift_name else 2)
        # 시간대 정렬 (0: 오픈, 1: 미들, 2: 마감)
        time_order = 0 if '오픈' in shift_name else (1 if '미들' in shift_name else 2)
        return (day_order, time_order)
    
    # 모든 직원 목록
    employees = list(Employee.objects.select_related(
        'department', 'shift'
    ).all())
    
    # 정렬: 요일 -> 시간대
    employees.sort(key=sort_employee_key)
    
    # 역할 설정
    role_settings = RoleSetting.objects.all()
    
    # 최대/최소 급여 설정
    max_settings = MaxSetting.objects.all()
    
    # 구인 슬롯 - 요일별로 분리하되 같은 요일+시간+타입은 그룹화
    all_slots = HiringSlot.objects.select_related('shift').order_by('shift__time_range')
    
    # shift의 time_range, type, days를 기준으로 그룹화
    grouped_slots = {}
    for slot in all_slots:
        # 월화수, 목금, 토일 정보 추출
        days_key = None
        if '월화수' in slot.shift.name:
            days_key = '월화수'
        elif '목금' in slot.shift.name:
            days_key = '목금'
        elif '토일' in slot.shift.name:
            days_key = '토일'
        
        if not days_key:
            continue
            
        # Type 추출
        type_key = None
        if '오픈' in slot.shift.name:
            type_key = '오픈'
        elif '마감' in slot.shift.name:
            type_key = '마감'
        elif '미들' in slot.shift.name:
            type_key = '미들'
        
        if not type_key:
            continue
        
        # time_range, type, days를 모두 키로 사용하여 요일별로 분리
        key = (slot.shift.time_range, type_key, days_key)
        
        if key not in grouped_slots:
            grouped_slots[key] = {
                'time_range': slot.shift.time_range,
                'type': type_key,
                'days': days_key,
                'slots': []
            }
        
        grouped_slots[key]['slots'].append(slot)
    
    # 리스트로 변환
    hiring_slots = []
    for group in grouped_slots.values():
        # 첫 번째 슬롯을 대표로 사용
        group['representative_slot'] = group['slots'][0]
        hiring_slots.append(group)
    
    # 요일 순서 정의
    day_order = {'월화수': 0, '목금': 1, '토일': 2}
    # 요일순, 시간순으로 정렬
    hiring_slots.sort(key=lambda x: (day_order.get(x['days'], 999), x['time_range']))
    
    context = {
        'employees': employees,
        'role_settings': role_settings,
        'max_settings': max_settings,
        'hiring_slots': hiring_slots,
    }
    
    return render(request, 'employees.html', context)


def employee_form_view(request, pk=None):
    """직원 생성/수정 폼"""
    employee = None
    if pk:
        employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        # 폼 데이터 수집
        full_name = request.POST.get('full_name')
        shift_id = request.POST.get('shift')
        phone = request.POST.get('phone')
        birth_year = request.POST.get('birth_year')
        favorite_color = request.POST.get('favorite_color')
        address = request.POST.get('address')
        attendance_pin = request.POST.get('attendance_pin')
        role = request.POST.get('role')
        wage = request.POST.get('wage')
        wage_type = request.POST.get('wage_type', 'hourly')
        memo = request.POST.get('memo', '')
        color_tag = request.POST.get('color_tag')
        
        # 이미지 파일 처리
        image = request.FILES.get('image')
        
        try:
            # 기본 부서 할당 (첨 번째 부서 또는 '관리' 부서)
            department = Department.objects.first()
            if not department:
                department = Department.objects.create(name='관리')
            
            # Shift 가져오기 (매니저는 선택 사항)
            shift = None
            if shift_id:
                shift = Shift.objects.get(pk=shift_id)
            elif role != 'manager':
                raise Exception('근무 시간을 선택해주세요.')
            
            if employee:
                # 수정
                employee.full_name = full_name
                employee.department = department
                employee.shift = shift
                employee.phone = phone
                employee.birth_year = birth_year
                employee.favorite_color = favorite_color
                employee.address = address
                employee.attendance_pin = attendance_pin
                employee.role = role
                employee.wage = wage
                employee.wage_type = wage_type
                employee.memo = memo
                employee.color_tag = color_tag
                if image:
                    employee.image = image
                employee.save()
                messages.success(request, f'{full_name} 직원 정보가 수정되었습니다.')
            else:
                # 생성
                employee = Employee.objects.create(
                    full_name=full_name,
                    department=department,
                    shift=shift,
                    phone=phone,
                    birth_year=birth_year,
                    favorite_color=favorite_color,
                    address=address,
                    attendance_pin=attendance_pin,
                    role=role,
                    wage=wage,
                    wage_type=wage_type,
                    memo=memo,
                    color_tag=color_tag,
                    image=image if image else None
                )
                messages.success(request, f'{full_name} 직원이 등록되었습니다.')
            
            # 해당 shift의 구인 슬롯을 구인완료로 변경
            hiring_slots = HiringSlot.objects.filter(shift=shift)
            for slot in hiring_slots:
                slot.status = 'filled'
                slot.save()
            
            return redirect('employees')
        
        except Exception as e:
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    
    # GET 요청 - 폼 표시
    # HiringSlot에 있는 shift만 가져오기 (중복 제거)
    hiring_slots = HiringSlot.objects.select_related('shift').all()
    
    # shift의 name과 time_range를 기준으로 완전히 중복 제거
    shift_dict = {}
    for slot in hiring_slots:
        # Type 추출
        type_key = None
        if '오픈' in slot.shift.name:
            type_key = '오픈'
        elif '마감' in slot.shift.name:
            type_key = '마감'
        elif '미들' in slot.shift.name:
            type_key = '미들'
        
        # Days 추출
        days_key = None
        if '월화수' in slot.shift.name:
            days_key = '월화수'
        elif '목금' in slot.shift.name:
            days_key = '목금'
        elif '토일' in slot.shift.name:
            days_key = '토일'
        
        if not type_key or not days_key:
            continue
        
        # 고유 키 생성
        key = (type_key, days_key, slot.shift.time_range)
        
        # 중복 제거 - 첫 번째 것만 사용
        if key not in shift_dict:
            shift_dict[key] = {
                'shift': slot.shift,
                'type': type_key,
                'days': days_key,
                'time_range': slot.shift.time_range
            }
    
    # 리스트로 변환하고 정렬
    shift_list = []
    for item in shift_dict.values():
        shift_list.append(item)
    
    # 요일순, 시간순으로 정렬
    day_order = {'월화수': 0, '목금': 1, '토일': 2}
    shift_list.sort(key=lambda x: (day_order.get(x['days'], 999), x['time_range']))
    
    # shift 객체만 추출
    unique_shifts = [item['shift'] for item in shift_list]
    
    # Role Settings 가져오기 (기본 급여 설정용)
    role_settings = RoleSetting.objects.all()
    
    context = {
        'employee': employee,
        'shifts': unique_shifts,
        'role_settings': role_settings,
    }
    
    return render(request, 'employee_form.html', context)


def employee_delete_view(request, pk):
    """직원 삭제"""
    employee = get_object_or_404(Employee, pk=pk)
    name = employee.full_name
    shift = employee.shift
    
    # 같은 shift를 사용하는 다른 직원이 있는지 확인
    same_shift_employees = Employee.objects.filter(shift=shift).exclude(pk=pk).count()
    
    employee.delete()
    messages.success(request, f'{name} 직원이 삭제되었습니다.')
    
    # 같은 shift를 사용하는 직원이 없으면 구인중으로 변경
    if same_shift_employees == 0:
        hiring_slots = HiringSlot.objects.filter(shift=shift)
        for slot in hiring_slots:
            slot.status = 'open'
            slot.save()
    
    return redirect('employees')
