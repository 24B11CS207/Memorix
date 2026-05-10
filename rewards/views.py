from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from accounts.models import Profile
from .models import Badge, PointEvent


@login_required
def rewards_home(request):
    badges = Badge.objects.filter(user=request.user).order_by('-earned_at')
    events = PointEvent.objects.filter(user=request.user)[:30]
    return render(request, 'rewards/home.html', {
        'badges': badges, 'events': events,
        'profile': request.user.profile,
    })


@login_required
def leaderboard(request):
    top = Profile.objects.select_related('user').order_by('-points')[:50]
    return render(request, 'rewards/leaderboard.html', {'top': top})
