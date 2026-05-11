from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import AnalyticsSnapshot
from .services import calculate_user_metrics, difficulty_for_score, record_analytics_snapshot
from exams.models import InstantTest
from revisions.models import RevisionPlan
from topics.models import Topic


class AnalyticsCalculationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='learner', password='StrongPass123')
        self.topic = Topic.objects.create(user=self.user, name='Chemistry')

    def test_difficulty_thresholds(self):
        self.assertEqual(difficulty_for_score(80), 'hard')
        self.assertEqual(difficulty_for_score(50), 'medium')
        self.assertEqual(difficulty_for_score(49.99), 'easy')

    def test_accuracy_retention_review_completion_and_weak_topics(self):
        InstantTest.objects.create(
            user=self.user,
            topic=self.topic,
            questions=[],
            total_questions=10,
            correct_count=4,
            score_percent=40,
            completed=True,
        )
        plan = RevisionPlan.create_with_schedule(self.user, self.topic, 4)
        first, second = list(plan.sessions.order_by('review_number')[:2])
        first.status = 'passed'
        first.completed_at = timezone.now()
        first.score_percent = 90
        first.save()
        second.status = 'failed'
        second.completed_at = timezone.now()
        second.score_percent = 40
        second.save()

        metrics = calculate_user_metrics(self.user)

        self.assertEqual(metrics['accuracy'], 40.0)
        self.assertEqual(metrics['retention'], 50.0)
        self.assertEqual(metrics['review_completion'], 25.0)
        self.assertEqual(metrics['weak_topics'][0]['name'], 'Chemistry')

    def test_record_analytics_snapshot_persists_metrics(self):
        snapshot = record_analytics_snapshot(self.user)

        self.assertIsInstance(snapshot, AnalyticsSnapshot)
        self.assertEqual(snapshot.user, self.user)
