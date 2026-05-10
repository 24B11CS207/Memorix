from django.contrib import admin
from .models import RevisionPlan, ReviewSession


class ReviewSessionInline(admin.TabularInline):
    model = ReviewSession
    extra = 0


@admin.register(RevisionPlan)
class RevisionPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'total_reviews', 'is_completed', 'started_at')
    list_filter = ('is_completed', 'total_reviews')
    inlines = [ReviewSessionInline]


@admin.register(ReviewSession)
class ReviewSessionAdmin(admin.ModelAdmin):
    list_display = ('plan', 'review_number', 'scheduled_date', 'status', 'score_percent', 'attempts')
    list_filter = ('status',)
