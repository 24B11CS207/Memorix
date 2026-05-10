import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
from topics.models import Topic
from exams.models import InstantTest
from revisions.models import ReviewSession


@login_required
def analytics_home(request):
    user = request.user

    topics = Topic.objects.filter(user=user)
    instant = InstantTest.objects.filter(user=user, completed=True)
    sessions = ReviewSession.objects.filter(plan__user=user)

    # Topic mastery: avg score per topic
    mastery = []
    for t in topics:
        avg = instant.filter(topic=t).aggregate(a=Avg('score_percent'))['a'] or 0
        mastery.append({'name': t.name, 'avg': round(avg, 1)})
    mastery.sort(key=lambda x: x['avg'], reverse=True)

    # Pass/fail ratio
    pass_count = instant.filter(score_percent__gte=80).count() + sessions.filter(status='passed').count()
    fail_count = instant.filter(score_percent__lt=80).count() + sessions.filter(status='failed').count()

    # Last 14 days activity heatmap-ish
    today = timezone.now().date()
    activity = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        c = instant.filter(completed_at__date=d).count() + sessions.filter(completed_at__date=d).count()
        activity.append({'date': d.strftime('%m-%d'), 'count': c})

    # Difficulty breakdown
    diff_breakdown = list(topics.values('difficulty').annotate(c=Count('id')))

    context = {
        'mastery_json': json.dumps(mastery),
        'pass_fail_json': json.dumps({'pass': pass_count, 'fail': fail_count}),
        'activity_json': json.dumps(activity),
        'difficulty_json': json.dumps(diff_breakdown),
        'total_topics': topics.count(),
        'completed_topics': topics.filter(is_completed=True).count(),
        'avg_accuracy': round(instant.aggregate(a=Avg('score_percent'))['a'] or 0, 1),
        'reviews_passed': sessions.filter(status='passed').count(),
        'reviews_total': sessions.count(),
    }
    return render(request, 'analytics/home.html', context)
