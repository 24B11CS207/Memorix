from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    """Extended user profile with credits, streaks, badges meta."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    email_verified = models.BooleanField(default=False)
    coins = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile<{self.user.username}>"

    @property
    def badge_level(self):
        """Return current badge tier based on points."""
        if self.points >= 1000:
            return 'Diamond'
        if self.points >= 600:
            return 'Gold'
        if self.points >= 300:
            return 'Silver'
        if self.points >= 100:
            return 'Bronze'
        return 'Beginner'

    def add_points(self, n):
        self.points = (self.points or 0) + n
        self.save(update_fields=['points'])

    def add_coins(self, n):
        self.coins = (self.coins or 0) + n
        self.save(update_fields=['coins'])

    def update_streak(self):
        """Increment streak when user is active on a new consecutive day."""
        today = timezone.now().date()
        if self.last_active_date == today:
            return
        if self.last_active_date and (today - self.last_active_date).days == 1:
            self.current_streak += 1
        else:
            self.current_streak = 1
        self.longest_streak = max(self.longest_streak, self.current_streak)
        self.last_active_date = today
        self.save(update_fields=['current_streak', 'longest_streak', 'last_active_date'])


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Token<{self.user.username}>"
