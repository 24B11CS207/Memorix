from django.contrib import admin
from .models import AIUsageLog


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'success', 'created_at')
    list_filter = ('kind', 'success')
    search_fields = ('user__username', 'note')
