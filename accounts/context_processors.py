def user_stats(request):
    """Make user profile stats available in every template."""
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        p = request.user.profile
        return {
            'user_profile': p,
            'user_coins': p.coins,
            'user_points': p.points,
            'user_streak': p.current_streak,
            'user_badge_level': p.badge_level,
        }
    return {}
