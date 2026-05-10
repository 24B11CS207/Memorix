from django.contrib import admin
from .models import Profile, EmailVerificationToken


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'coins', 'current_streak', 'badge_level', 'email_verified')
    search_fields = ('user__username', 'user__email')


@admin.register(EmailVerificationToken)
class EVTAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'used', 'created_at')
