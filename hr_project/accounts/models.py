from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """사용자 프로필 확장"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}"

class Store(models.Model):
    owner = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'store')
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
