from django.db import models
from employees.models import Employee
from schedule.constants import WORK_TIME, WORK_TYPE, WEEKDAYS, TIME_MAP

# 근무 스케줄 템플릿
class Schedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    work_type = models.IntegerField(choices=WORK_TYPE)
    work_day = models.IntegerField(choices=WEEKDAYS)
    work_time = models.IntegerField(choices=WORK_TIME)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default = True)

    def save(self, *args, **kwargs):
        # start_time, end_time 을 map과 대응 후 저장
        if (self.work_time is not None 
            and self.work_time in TIME_MAP
            and not (self.start_time and self.end_time)
        ): # NULL 방지
            self.start_time, self.end_time = TIME_MAP[self.work_time]
        super().save(*args, **kwargs)

    def __str__(self):
        time_range = (
            f"{self.start_time.strftime('%H:%M')}~{self.end_time.strftime('%H:%M')}"
            if self.start_time and self.end_time
            else "-"
        )
        return f"{self.employee.full_name} {self.get_work_day_display()} {time_range}"


# monthly 근무 스케줄
class DayWorkPlan(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='dayworkplans')
    schedule = models.ForeignKey (Schedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='day_work_plans')
    work_date=models.DateField()
    planned_start = models.TimeField(null=True, blank=True)
    planned_end = models.TimeField(null=True, blank=True)

    def __str__(self):
        time_range = (
            f"{self.planned_start.strftime('%H:%M')}~{self.planned_end.strftime('%H:%M')}"
            if self.planned_start and self.planned_end
            else "-"
        )
        return f"{self.employee.full_name} {self.work_date} {time_range}"
