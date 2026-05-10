"""Rewards service: points, coins, badge unlocking."""
from .models import Badge, PointEvent
from notifications.services import notify_badge_earned


TOPIC_BADGE_TIERS = [
    (10, 'topic_bronze', 'Topic Bronze', '🥉'),
    (25, 'topic_silver', 'Topic Silver', '🥈'),
    (50, 'topic_gold', 'Topic Gold', '🥇'),
    (100, 'topic_diamond', 'Topic Diamond', '💎'),
]

POINT_BADGE_TIERS = [
    (100, 'points_bronze', 'Bronze Achiever', '🥉'),
    (300, 'points_silver', 'Silver Achiever', '🥈'),
    (600, 'points_gold', 'Gold Achiever', '🥇'),
    (1000, 'points_diamond', 'Diamond Achiever', '💎'),
]

STREAK_BADGE_TIERS = [
    (7, 'streak_7', '7-Day Streak', '🔥'),
    (30, 'streak_30', '30-Day Streak', '🔥🔥'),
]


def grant_points(user, points, reason="", coins=0):
    profile = user.profile
    profile.add_points(points)
    if coins:
        profile.add_coins(coins)
    PointEvent.objects.create(user=user, points=points, reason=reason)
    _check_point_badges(user)


def grant_topic_completion_rewards(user):
    """Called when a user finishes a Topic. Adds points/coins, checks badges."""
    grant_points(user, 25, reason="Topic completed", coins=10)
    _check_topic_badges(user)


def _award_badge(user, kind, name, icon):
    badge, created = Badge.objects.get_or_create(
        user=user, kind=kind,
        defaults={'name': name, 'icon': icon},
    )
    if created:
        try:
            notify_badge_earned(user, name)
        except Exception:
            pass
    return badge, created


def _check_topic_badges(user):
    completed = user.topics.filter(is_completed=True).count()
    for threshold, kind, name, icon in TOPIC_BADGE_TIERS:
        if completed >= threshold:
            _award_badge(user, kind, name, icon)


def _check_point_badges(user):
    pts = user.profile.points
    for threshold, kind, name, icon in POINT_BADGE_TIERS:
        if pts >= threshold:
            _award_badge(user, kind, name, icon)


def check_streak_badges(user):
    streak = user.profile.current_streak
    for threshold, kind, name, icon in STREAK_BADGE_TIERS:
        if streak >= threshold:
            _award_badge(user, kind, name, icon)
