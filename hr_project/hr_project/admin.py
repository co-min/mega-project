from django.contrib import admin
from .models import UserProfile, Store, UserSettings


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    search_fields = ('user__username', 'user__email', 'role')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'address', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('name', 'address', 'owner__username')
    readonly_fields = ('created_at',)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'push_notifications', 'language', 'theme')
    list_filter = ('email_notifications', 'push_notifications', 'language', 'theme')
    search_fields = ('user__username',)
