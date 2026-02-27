from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """사용자 프로필 확장"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, default='가맹점주')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Store(models.Model):
    owner = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'store')
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # 알림 설정
    email_notifications = models.BooleanField(default=True, verbose_name='이메일 알림')
    push_notifications = models.BooleanField(default=True, verbose_name='푸시 알림')
    
    # 기본 설정
    language = models.CharField(max_length=10, default='ko', verbose_name='언어')
    theme = models.CharField(max_length=10, default='light', choices=[('light', '라이트'), ('dark', '다크')], verbose_name='테마')
    
    def __str__(self):
        return f"{self.user.username} - 설정"
