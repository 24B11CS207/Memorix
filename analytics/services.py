from django.db.models import Avg

from .models import AnalyticsSnapshot
from exams.models import InstantTest
from revisions.models import ReviewSession
from topics.models import Topic


def difficulty_for_score(score):
    if score >= 80:
        return 'hard'
    if score >= 50:
        return 'medium'
    return 'easy'


def update_topic_difficulty(topic, score):
    difficulty = difficulty_for_score(score)
    if topic.difficulty != difficulty:
        topic.difficulty = difficulty
        topic.save(update_fields=['difficulty', 'updated_at'])
    return difficulty


def calculate_user_metrics(user):
    tests = InstantTest.objects.filter(user=user, completed=True)
    sessions = ReviewSession.objects.filter(plan__user=user)
    completed_sessions = sessions.exclude(completed_at__isnull=True)

    total_questions = sum(test.total_questions for test in tests)
    correct_answers = sum(test.correct_count for test in tests)
    accuracy = round((correct_answers / total_questions) * 100, 2) if total_questions else 0.0

    completed_review_count = completed_sessions.count()
    passed_review_count = completed_sessions.filter(status='passed').count()
    retention = round((passed_review_count / completed_review_count) * 100, 2) if completed_review_count else 0.0

    total_reviews = sessions.count()
    review_completion = round((passed_review_count / total_reviews) * 100, 2) if total_reviews else 0.0

    weak_topics = []
    for topic in Topic.objects.filter(user=user):
        avg_score = tests.filter(topic=topic).aggregate(avg=Avg('score_percent'))['avg']
        if avg_score is not None and avg_score < 50:
            weak_topics.append({
                'id': topic.id,
                'name': topic.name,
                'score': round(avg_score, 2),
            })

    weak_topics.sort(key=lambda item: item['score'])
    return {
        'accuracy': accuracy,
        'retention': retention,
        'review_completion': review_completion,
        'weak_topics': weak_topics,
    }


def record_analytics_snapshot(user):
    metrics = calculate_user_metrics(user)
    return AnalyticsSnapshot.objects.create(user=user, **metrics)
