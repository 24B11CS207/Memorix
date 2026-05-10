class StreakMiddleware:
    """Update the user's streak on every authenticated request (once per day)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if request.user.is_authenticated and hasattr(request.user, 'profile'):
                request.user.profile.update_streak()
        except Exception:
            pass
        return response
