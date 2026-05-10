from django.db import models
from django.contrib.auth.models import User


class AIUsageLog(models.Model):
    KIND_CHOICES = [
        ('modules', 'Modules'),
        ('mcq', 'MCQ Generation'),
        ('explain', 'Explanation'),
        ('chat', 'Chatbot'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    success = models.BooleanField(default=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['-created_at'])]

    def __str__(self):
        return f"{self.kind} by {self.user} @ {self.created_at:%Y-%m-%d}"
