from django.db import models
from employees.models import Employee
from datetime import time

#근무 스케줄 템플릿
class Schedule(models.Model):
    #근무 유형
    WORK_TYPE = [
        (0, '오픈'),
        (1, '미들'),
        (2, '마감'),
    ]

    #근무 요일
    WEEKDAYS = [
        (0, '월'),
        (1, '화'),
        (2, '수'),
        (3, '목'),
        (4, '금'),
        (5, '토'),
        (6, '일'),
    ]

    #근무 시간대 선택
    WORK_TIME = [
        #평일
        (0, '8:00 - 10:00'),
        (1, '8:00 - 14:00'),
        (2, '11:00 - 15:00'),
        (3, '18:00 - 22:00'),
        #주말
        (4, '8:30 - 14:30'),
        (5, '10:00 - 16:00'),
        (6, '14:00 - 20:00'),
        (7, '16:00 - 22:00')
    ]
    #근무 시간 map
    TIME_MAP = {
        #평일
        0: (time(8,0),time(10,0)),
        1: (time(8,0),time(14,0)),
        2: (time(11,0),time(15,0)),
        3: (time(18,0),time(22,0)),
        #주말
        4: (time(8,30),time(14,30)),
        5: (time(10,0),time(16,0)),
        6: (time(14,0),time(20,0)),
        7: (time(16,0),time(22,0)),
    }

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    work_type = models.IntegerField(choices=WORK_TYPE)
    weekday = models.IntegerField(choices=WEEKDAYS)

    #사용자 선택
    work_time = models.IntegerField(choices=WORK_TIME)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    is_active = models.BooleanField(default = True)

    def save(self, *args, **kwargs):
        # NULL 방지
        if (self.work_time is not None
            and self.work_time in self.TIME_MAP
            and not (self.start_time and self.end_time)
        ):
            self.start_time, self.end_time = self.TIME_MAP[self.work_time]
        super().save(*args, **kwargs)

    def __str__(self):
        time_range = (
            f"{self.start_time.strftime('%H:%M')}~{self.end_time.strftime('%H:%M')}"
            if self.planned_start and self.planned_end
            else "-"
        )
        return f"{self.employee.full_name} {self.get_weekday_display()} {time_range}"


#실제 근무 스케줄
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



"""
      #캘린더에 표시되는 UI 이벤트
class Event(models.Model):
    COLOR_CHOICES = (
        ('red', 'red'),
        ('blue', 'blue'),
        ('green', 'green'),
        ('purple', 'purple'),
        ('yellow', 'yellow'),
    )
    name = models.CharField(max_length=50)
    date = models.DateField()
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='blue')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')

    def __str__(self):
        return f"{self.name} {self.date}"


class Announcement(models.Model):
    title = models.CharField(max_length=100)
    date = models.DateField()
    body = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} ({self.date})"

"""