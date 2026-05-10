from django.db import models
from django.contrib.auth.models import User
from topics.models import Topic


class InstantTest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='instant_tests')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='instant_tests')
    questions = models.JSONField(default=list)  # snapshot of generated MCQs
    answers = models.JSONField(default=dict, blank=True)  # {question_index: chosen_index}
    score_percent = models.FloatField(default=0.0)
    correct_count = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    time_taken_seconds = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f"InstantTest<{self.user.username}, {self.topic.name}>"
