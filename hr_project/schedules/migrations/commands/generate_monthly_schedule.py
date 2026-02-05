from django.core.management.base import BaseCommand
from datetime import date, relativedelta
from schedules.views import create_monthly_schedule

# 전 날 말일에 다음 달 스케줄 미리 생성
class Command(BaseCommand):
    help = 'Generate monthly work schedule'

    def handle(self, *args, **kwargs):
        today = date.today()
        next_month_date = today+relativedelta(months=1)
        create_monthly_schedule(next_month_date.year, next_month_date.month)
        self.stdout.write(self.style.SUCCESS('Schedule generated'))
