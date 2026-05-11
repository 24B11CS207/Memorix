from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import LearningModule, ModuleQuestion, Topic


def module_payload(count=2):
    return [
        {
            'title': f'Module {index + 1}',
            'content': 'AI explanation content.',
            'key_points': ['Point 1', 'Point 2'],
            'examples': ['Example 1'],
            'summary': 'Short summary.',
            'reading_minutes': 5,
        }
        for index in range(count)
    ]


def question_payload(prefix='Question', count=5):
    return [
        {
            'question': f'{prefix} {index + 1}',
            'options': ['Correct', 'Wrong 1', 'Wrong 2', 'Wrong 3'],
            'correct_index': 0,
            'explanation': 'Because it is correct.',
            'confusion_note': '',
        }
        for index in range(count)
    ]


class TopicAiGenerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='learner', password='StrongPass123')
        self.client.force_login(self.user)

    @patch('topics.views.generate_unique_mcqs')
    @patch('topics.views.generate_learning_modules')
    @patch('topics.views.generate_topic_explanation')
    def test_topic_creation_stores_ai_explanation_and_questions(
        self,
        mocked_explanation,
        mocked_modules,
        mocked_questions,
    ):
        mocked_explanation.return_value = 'Generated topic explanation.'
        mocked_modules.return_value = module_payload(2)
        mocked_questions.side_effect = [
            question_payload('Module one question', 5),
            question_payload('Module two question', 5),
        ]

        response = self.client.post(reverse('topics:create'), {
            'name': 'Algebra',
            'difficulty': 'medium',
            'description': 'Focus on equations.',
        })

        self.assertEqual(response.status_code, 302)
        topic = Topic.objects.get(user=self.user, name='Algebra')
        self.assertEqual(topic.ai_explanation, 'Generated topic explanation.')
        self.assertEqual(LearningModule.objects.filter(topic=topic).count(), 2)
        self.assertEqual(ModuleQuestion.objects.filter(module__topic=topic).count(), 10)
        self.assertEqual(mocked_questions.call_count, 2)
        self.assertEqual(mocked_questions.call_args.kwargs['previous_questions'][-1], 'Module one question 5')
