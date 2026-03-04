from django.contrib import admin
from .models import UserProfile, Store


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__email',)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'address','created_at')
    search_fields = ('name', 'address', 'owner__username')
    readonly_fields = ('created_at',)  