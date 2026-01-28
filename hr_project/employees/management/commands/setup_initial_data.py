from django.core.management.base import BaseCommand
from employees.models import Department, Shift, RoleSetting, MaxSetting, HiringSlot


class Command(BaseCommand):
    help = '초기 데이터 (부서, 근무시간, 역할설정, 급여설정, 구인슬롯) 설정'

    def handle(self, *args, **kwargs):
        # 부서 생성
        departments = ['커피', '베이커리', '주방', '홀서빙', '관리']
        for dept_name in departments:
            dept, created = Department.objects.get_or_create(name=dept_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ 부서 생성: {dept_name}'))
            else:
                self.stdout.write(f'  부서 존재: {dept_name}')

        # 근무시간 생성
        shifts_data = [
            {'name': '평일 오픈 월화수 (08:00-16:00)', 'days': 'weekday_open', 'time_range': '08:00-16:00'},
            {'name': '평일 마감 월화수 (14:00-22:00)', 'days': 'weekday_close', 'time_range': '14:00-22:00'},
            {'name': '평일 오픈 목금 (08:00-16:00)', 'days': 'weekday_open', 'time_range': '08:00-16:00'},
            {'name': '평일 마감 목금 (14:00-22:00)', 'days': 'weekday_close', 'time_range': '14:00-22:00'},
            {'name': '주말 오픈 토일 (08:00-16:00)', 'days': 'weekend_open', 'time_range': '08:00-16:00'},
            {'name': '주말 미들 토일 (12:00-20:00)', 'days': 'weekend_middle', 'time_range': '12:00-20:00'},
            {'name': '주말 마감 토일 (16:00-24:00)', 'days': 'weekend_close', 'time_range': '16:00-24:00'},
        ]

        shifts_list = []
        for shift_data in shifts_data:
            shift, created = Shift.objects.get_or_create(
                name=shift_data['name'],
                defaults={
                    'days': shift_data['days'],
                    'time_range': shift_data['time_range']
                }
            )
            shifts_list.append(shift)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ 근무시간 생성: {shift_data["name"]}'))
            else:
                self.stdout.write(f'  근무시간 존재: {shift_data["name"]}')

        # 역할 설정 생성
        roles_data = [
            {'role': '파트타임', 'base_wage': 10030, 'wage_type': 'hourly', 'increase_per_6_month': 500},
            {'role': '매니저', 'base_wage': 2600000, 'wage_type': 'monthly', 'increase_per_6_month': 0},
            {'role': '대체근무', 'base_wage': 11500, 'wage_type': 'hourly', 'increase_per_6_month': 0},
        ]

        for role_data in roles_data:
            role, created = RoleSetting.objects.get_or_create(
                role=role_data['role'],
                defaults={
                    'base_wage': role_data['base_wage'],
                    'wage_type': role_data['wage_type'],
                    'increase_per_6_month': role_data['increase_per_6_month']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ 역할설정 생성: {role_data["role"]}'))
            else:
                self.stdout.write(f'  역할설정 존재: {role_data["role"]}')

        # 최대/최소 급여 설정 생성
        if not MaxSetting.objects.exists():
            MaxSetting.objects.create(
                max_wage=15030,  # 최저시급 + 5000
                min_wage=10030   # 최저시급
            )
            self.stdout.write(self.style.SUCCESS('✓ 최대/최소 급여 설정 생성'))
        else:
            self.stdout.write('  최대/최소 급여 설정 존재')

        # 구인 슬롯 생성
        for shift in shifts_list:
            dept = Department.objects.first()
            if dept:
                slot, created = HiringSlot.objects.get_or_create(
                    department=dept,
                    shift=shift,
                    defaults={'status': 'open'}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✓ 구인슬롯 생성: {shift.name}'))
                else:
                    self.stdout.write(f'  구인슬롯 존재: {shift.name}')

        self.stdout.write(self.style.SUCCESS('\n초기 데이터 설정이 완료되었습니다!'))

