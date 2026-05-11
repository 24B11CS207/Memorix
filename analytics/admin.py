from django.contrib import admin

from .models import AnalyticsSnapshot


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'accuracy', 'retention', 'review_completion', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)
