from django.contrib import admin
from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'topic', 'updated_at')
    search_fields = ('title', 'body', 'user__username')
