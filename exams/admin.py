from django.contrib import admin
from .models import InstantTest


@admin.register(InstantTest)
class InstantTestAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'score_percent', 'completed', 'created_at')
    list_filter = ('completed',)
    search_fields = ('user__username', 'topic__name')
