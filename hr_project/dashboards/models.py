from django.db import models
from employees.models import Employee

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
