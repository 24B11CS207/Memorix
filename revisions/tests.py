from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import RevisionPlan, ReviewSession
from analytics.models import AnalyticsSnapshot
from topics.models import Topic


def sample_questions(count=5):
    return [
        {
            'question': f'Review question {index + 1}',
            'options': ['Correct', 'Wrong 1', 'Wrong 2', 'Wrong 3'],
            'correct_index': 0,
            'explanation': 'Correct is right.',
            'confusion_note': '',
        }
        for index in range(count)
    ]


class ReviewSchedulingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='learner', password='StrongPass123')
        self.topic = Topic.objects.create(user=self.user, name='Physics', difficulty='medium')
        self.client.force_login(self.user)

    def test_revision_plan_creates_expected_schedule(self):
        plan = RevisionPlan.create_with_schedule(self.user, self.topic, 4)

        self.assertEqual(plan.sessions.count(), 4)
        self.assertEqual(
            list(plan.sessions.order_by('review_number').values_list('review_number', flat=True)),
            [1, 2, 3, 4],
        )

    @patch('revisions.views.generate_wrong_answer_explanation')
    def test_review_submission_records_analytics_and_adjusts_difficulty(self, mocked_explanation):
        mocked_explanation.return_value = 'Review the topic again.'
        plan = RevisionPlan.create_with_schedule(self.user, self.topic, 4)
        session = plan.sessions.order_by('review_number').first()
        session.questions = sample_questions(5)
        session.status = 'available'
        session.save()

        response = self.client.post(reverse('revisions:take_review', args=[session.id]), {
            'q_0': '0',
            'q_1': '0',
            'q_2': '1',
            'q_3': '1',
            'q_4': '1',
        })

        self.assertEqual(response.status_code, 302)
        session.refresh_from_db()
        self.topic.refresh_from_db()
        self.assertEqual(session.status, 'failed')
        self.assertEqual(session.score_percent, 40.0)
        self.assertEqual(self.topic.difficulty, 'easy')
        self.assertTrue(AnalyticsSnapshot.objects.filter(user=self.user).exists())
        self.assertTrue(
            ReviewSession.objects.filter(plan=plan, review_number=2).first().scheduled_date
            > session.scheduled_date
        )
