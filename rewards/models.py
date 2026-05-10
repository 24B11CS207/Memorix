from django.db import models
from django.contrib.auth.models import User


class Badge(models.Model):
    KIND_CHOICES = [
        ('topic_bronze', 'Topic Bronze (10 topics)'),
        ('topic_silver', 'Topic Silver (25 topics)'),
        ('topic_gold', 'Topic Gold (50 topics)'),
        ('topic_diamond', 'Topic Diamond (100 topics)'),
        ('points_bronze', 'Points Bronze (100)'),
        ('points_silver', 'Points Silver (300)'),
        ('points_gold', 'Points Gold (600)'),
        ('points_diamond', 'Points Diamond (1000)'),
        ('streak_7', '7-Day Streak'),
        ('streak_30', '30-Day Streak'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    kind = models.CharField(max_length=30, choices=KIND_CHOICES)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default='🏅')
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'kind')
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.name} for {self.user.username}"


class PointEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_events')
    points = models.IntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: +{self.points} ({self.reason})"
