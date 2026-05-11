from django.db import models
from django.contrib.auth.models import User


class Topic(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    description = models.TextField(blank=True)
    ai_explanation = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    accuracy_percent = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f"{self.name} ({self.difficulty})"

    @property
    def total_modules(self):
        return self.modules.count()

    @property
    def completed_modules_count(self):
        return self.modules.filter(is_completed=True).count()

    @property
    def progress_percent(self):
        total = self.total_modules
        return int((self.completed_modules_count / total) * 100) if total else 0


class LearningModule(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='modules')
    order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=255)
    content = models.TextField()
    key_points = models.JSONField(default=list, blank=True)
    examples = models.JSONField(default=list, blank=True)
    summary = models.TextField(blank=True)
    reading_minutes = models.PositiveIntegerField(default=5)
    is_completed = models.BooleanField(default=False)
    is_unlocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.topic.name} – {self.title}"


class ModuleQuestion(models.Model):
    """2-mark mini test questions per learning module."""
    module = models.ForeignKey(LearningModule, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    options = models.JSONField(default=list)  # list of 4 strings
    correct_index = models.PositiveSmallIntegerField()
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Q for {self.module.title}"


class ModuleAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(LearningModule, on_delete=models.CASCADE, related_name='attempts')
    score_percent = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.user.username} – {self.module.title} – {self.score_percent}%"
