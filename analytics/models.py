from django.conf import settings
from django.db import models


class AnalyticsSnapshot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='analytics_snapshots')
    accuracy = models.FloatField(default=0.0)
    retention = models.FloatField(default=0.0)
    review_completion = models.FloatField(default=0.0)
    weak_topics = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"AnalyticsSnapshot<{self.user}, {self.created_at:%Y-%m-%d %H:%M}>"
