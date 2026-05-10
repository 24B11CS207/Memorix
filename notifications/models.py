from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    KIND_CHOICES = [
        ('login', 'Login'),
        ('welcome', 'Welcome'),
        ('test', 'Test Completion'),
        ('review', 'Review Reminder'),
        ('streak', 'Streak'),
        ('badge', 'Badge Earned'),
        ('system', 'System'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='system')
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f"{self.kind}: {self.title}"
