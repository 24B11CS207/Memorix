from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'title', 'is_read', 'email_sent', 'created_at')
    list_filter = ('kind', 'is_read', 'email_sent')
    search_fields = ('user__username', 'title')
