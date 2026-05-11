from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from ai_engine.services import generate_mcqs, generate_unique_mcqs
from analytics.models import AnalyticsSnapshot
from .models import InstantTest
from topics.models import Topic


def sample_questions(count=5):
    return [
        {
            'question': f'Question {index + 1}',
            'options': ['Correct', 'Wrong 1', 'Wrong 2', 'Wrong 3'],
            'correct_index': 0,
            'explanation': 'Correct is right.',
            'confusion_note': '',
        }
        for index in range(count)
    ]


@override_settings(GEMINI_API_KEY='', AZURE_OPENAI_API_KEY='', AZURE_OPENAI_ENDPOINT='')
class McqGenerationTests(TestCase):
    def test_fallback_mcq_generation_has_valid_shape(self):
        questions = generate_mcqs('Algebra', count=3, difficulty='easy')

        self.assertEqual(len(questions), 3)
        self.assertTrue(all(len(question['options']) == 4 for question in questions))
        self.assertTrue(all(0 <= question['correct_index'] <= 3 for question in questions))

    def test_unique_mcq_generation_filters_previous_questions(self):
        questions = generate_unique_mcqs(
            'Algebra',
            count=3,
            difficulty='easy',
            previous_questions=['Sample question 1 about Algebra: which option best describes the core idea?'],
        )

        question_texts = {question['question'] for question in questions}
        self.assertEqual(len(question_texts), 3)
        self.assertNotIn('Sample question 1 about Algebra: which option best describes the core idea?', question_texts)


class InstantExamTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='learner', password='StrongPass123')
        self.topic = Topic.objects.create(user=self.user, name='Algebra', difficulty='medium')
        self.client.force_login(self.user)

    @patch('exams.views.generate_unique_mcqs')
    def test_start_exam_uses_current_topic_difficulty(self, mocked_generate):
        mocked_generate.return_value = sample_questions(3)

        response = self.client.get(reverse('exams:start', args=[self.topic.id]))

        self.assertEqual(response.status_code, 302)
        mocked_generate.assert_called_once()
        self.assertEqual(mocked_generate.call_args.kwargs['difficulty'], 'medium')
        self.assertTrue(InstantTest.objects.filter(user=self.user, topic=self.topic).exists())

    @patch('exams.views.generate_wrong_answer_explanation')
    def test_exam_submission_updates_difficulty_and_analytics(self, mocked_explanation):
        mocked_explanation.return_value = 'Review the core concept.'
        test = InstantTest.objects.create(
            user=self.user,
            topic=self.topic,
            questions=sample_questions(5),
            total_questions=5,
        )

        response = self.client.post(reverse('exams:take', args=[test.id]), {
            'q_0': '0',
            'q_1': '0',
            'q_2': '0',
            'q_3': '0',
            'q_4': '1',
            'time_taken': '45',
        })

        self.assertEqual(response.status_code, 302)
        test.refresh_from_db()
        self.topic.refresh_from_db()
        self.assertTrue(test.completed)
        self.assertEqual(test.score_percent, 80.0)
        self.assertEqual(self.topic.difficulty, 'hard')
        self.assertTrue(AnalyticsSnapshot.objects.filter(user=self.user).exists())
