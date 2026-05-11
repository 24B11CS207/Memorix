from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from topics.models import Topic
from exams.models import InstantTest
from revisions.models import ReviewSession
from rewards.models import Badge
from analytics.services import calculate_user_metrics


EDUCATION_CATEGORIES = [
    {
        'title': 'School Classes',
        'subtitle': 'Class 1 to Class 10',
        'icon': 'bi-backpack',
        'items': [
            {'name': f'Class {i}', 'description': f'Core subjects and practice plan for Class {i}.', 'difficulty': 'easy' if i <= 5 else 'medium'}
            for i in range(1, 11)
        ],
    },
    {
        'title': 'Intermediate',
        'subtitle': 'Choose your stream',
        'icon': 'bi-diagram-3',
        'items': [
            {'name': 'Intermediate MPC', 'description': 'Mathematics, Physics, and Chemistry preparation.', 'difficulty': 'medium'},
            {'name': 'Intermediate BiPC', 'description': 'Biology, Physics, and Chemistry preparation.', 'difficulty': 'medium'},
            {'name': 'Intermediate HEC', 'description': 'History, Economics, and Civics preparation.', 'difficulty': 'medium'},
            {'name': 'Intermediate CEC', 'description': 'Commerce, Economics, and Civics preparation.', 'difficulty': 'medium'},
            {'name': 'Intermediate MEC', 'description': 'Mathematics, Economics, and Commerce preparation.', 'difficulty': 'medium'},
        ],
    },
    {
        'title': 'B.Tech',
        'subtitle': 'Engineering branches',
        'icon': 'bi-cpu',
        'items': [
            {'name': 'B.Tech CSE', 'description': 'Computer Science and Engineering roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Tech AI & ML', 'description': 'Artificial Intelligence and Machine Learning roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Tech Data Science', 'description': 'Data Science engineering roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Tech ECE', 'description': 'Electronics and Communication Engineering roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Tech EEE', 'description': 'Electrical and Electronics Engineering roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Tech Mechanical', 'description': 'Mechanical Engineering roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Tech Civil', 'description': 'Civil Engineering roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Tech IT', 'description': 'Information Technology engineering roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Tech Chemical', 'description': 'Chemical Engineering roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Tech Biotechnology', 'description': 'Biotechnology Engineering roadmap.', 'difficulty': 'hard'},
        ],
    },
    {
        'title': 'Medical',
        'subtitle': 'MBBS and healthcare',
        'icon': 'bi-heart-pulse',
        'items': [
            {'name': 'MBBS', 'description': 'Medical foundation and MBBS subject roadmap.', 'difficulty': 'hard'},
            {'name': 'BDS', 'description': 'Dental science foundation roadmap.', 'difficulty': 'hard'},
            {'name': 'B.Pharmacy', 'description': 'Pharmaceutical sciences roadmap.', 'difficulty': 'hard'},
            {'name': 'Nursing', 'description': 'Nursing concepts and clinical preparation.', 'difficulty': 'medium'},
            {'name': 'Physiotherapy', 'description': 'Physiotherapy foundation roadmap.', 'difficulty': 'medium'},
        ],
    },
    {
        'title': 'Other Education',
        'subtitle': 'Popular degree paths',
        'icon': 'bi-mortarboard',
        'items': [
            {'name': 'Degree B.Sc', 'description': 'Bachelor of Science subject planning.', 'difficulty': 'medium'},
            {'name': 'Degree B.Com', 'description': 'Commerce degree subject planning.', 'difficulty': 'medium'},
            {'name': 'Degree B.A', 'description': 'Arts degree subject planning.', 'difficulty': 'medium'},
            {'name': 'BBA', 'description': 'Business administration foundation roadmap.', 'difficulty': 'medium'},
            {'name': 'Law', 'description': 'Law subjects and exam preparation roadmap.', 'difficulty': 'hard'},
            {'name': 'Competitive Exams', 'description': 'Foundation plan for competitive exam preparation.', 'difficulty': 'hard'},
        ],
    },
]


@login_required
def dashboard_home(request):
    user = request.user
    topics = Topic.objects.filter(user=user)
    total_topics = topics.count()
    completed_topics = topics.filter(is_completed=True).count()
    pending_topics = total_topics - completed_topics

    instant_tests = InstantTest.objects.filter(user=user, completed=True)
    avg_accuracy = instant_tests.aggregate(a=Avg('score_percent'))['a'] or 0.0

    review_sessions = ReviewSession.objects.filter(plan__user=user)
    reviews_completed = review_sessions.filter(status='passed').count()
    reviews_total = review_sessions.count()
    today = timezone.now().date()
    due_today = review_sessions.filter(scheduled_date__lte=today).exclude(status='passed').count()

    # strong / weak topics: by average instant test score
    topic_scores = []
    for t in topics:
        avg = InstantTest.objects.filter(user=user, topic=t, completed=True).aggregate(a=Avg('score_percent'))['a']
        if avg is not None:
            topic_scores.append((t, round(avg, 1)))
    topic_scores.sort(key=lambda x: x[1], reverse=True)
    strong_topics = topic_scores[:3]
    weak_topics = topic_scores[-3:][::-1] if len(topic_scores) > 3 else topic_scores[::-1][:3]

    # last 7 days activity for chart
    last7 = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        c = InstantTest.objects.filter(user=user, completed=True, completed_at__date=d).count()
        c += review_sessions.filter(completed_at__date=d).count()
        last7.append({'date': d.strftime('%a'), 'count': c})

    badges = Badge.objects.filter(user=user).order_by('-earned_at')[:10]
    analytics_metrics = calculate_user_metrics(user)

    context = {
        'total_topics': total_topics,
        'completed_topics': completed_topics,
        'pending_topics': pending_topics,
        'avg_accuracy': round(avg_accuracy, 1),
        'reviews_completed': reviews_completed,
        'reviews_total': reviews_total,
        'reviews_due_today': due_today,
        'strong_topics': strong_topics,
        'weak_topics': weak_topics,
        'last7': last7,
        'badges': badges,
        'recent_tests': instant_tests.order_by('-completed_at')[:5],
        'education_categories': EDUCATION_CATEGORIES,
        'retention_percent': analytics_metrics['retention'],
        'review_completion_percent': analytics_metrics['review_completion'],
        'tracked_weak_topics': analytics_metrics['weak_topics'][:5],
    }
    return render(request, 'dashboard/home.html', context)
