from django.contrib import admin
from .models import Badge, PointEvent


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'kind', 'earned_at')
    list_filter = ('kind',)
    search_fields = ('user__username',)


@admin.register(PointEvent)
class PointEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'reason', 'created_at')
    search_fields = ('user__username', 'reason')
