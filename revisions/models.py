from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from topics.models import Topic


REVIEW_SCHEDULES = {
    4: [1, 3, 6, 10],
    5: [1, 3, 6, 10, 15],
    6: [1, 3, 6, 10, 15, 21],
}


class RevisionPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='revision_plans')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='revision_plans')
    total_reviews = models.PositiveSmallIntegerField()  # 4, 5, or 6
    started_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"RevisionPlan<{self.user.username}, {self.topic.name}, {self.total_reviews}R>"

    @classmethod
    def create_with_schedule(cls, user, topic, total_reviews):
        plan = cls.objects.create(user=user, topic=topic, total_reviews=total_reviews)
        offsets = REVIEW_SCHEDULES[total_reviews]
        today = timezone.now().date()
        for i, offset in enumerate(offsets):
            ReviewSession.objects.create(
                plan=plan,
                review_number=i + 1,
                scheduled_date=today + timedelta(days=offset - 1),  # offset 1 = today
            )
        return plan


class ReviewSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('available', 'Available'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ]
    plan = models.ForeignKey(RevisionPlan, on_delete=models.CASCADE, related_name='sessions')
    review_number = models.PositiveSmallIntegerField()
    scheduled_date = models.DateField()
    questions = models.JSONField(default=list, blank=True)
    answers = models.JSONField(default=dict, blank=True)
    score_percent = models.FloatField(default=0.0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['scheduled_date', 'review_number']
        indexes = [models.Index(fields=['plan', 'review_number'])]

    def __str__(self):
        return f"Review {self.review_number} of {self.plan} on {self.scheduled_date}"

    @property
    def is_due(self):
        return self.scheduled_date <= timezone.now().date() and self.status in ('pending', 'available', 'failed')

    def shift_future_sessions(self, days=1):
        """When a session fails, push all later, not-yet-passed sessions by N days."""
        for s in ReviewSession.objects.filter(
            plan=self.plan, review_number__gt=self.review_number
        ).exclude(status='passed'):
            s.scheduled_date = s.scheduled_date + timedelta(days=days)
            s.save(update_fields=['scheduled_date'])
