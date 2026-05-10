"""Create a demo user and a sample topic with modules — useful for first-run demos."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from topics.models import Topic, LearningModule, ModuleQuestion
from ai_engine.services import _fallback_modules, _fallback_mcqs


class Command(BaseCommand):
    help = "Seed the DB with a demo user and a sample topic."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username='demo',
            defaults={'email': 'demo@dqms.local', 'first_name': 'Demo'},
        )
        if created:
            user.set_password('demo12345')
            user.save()
            self.stdout.write(self.style.SUCCESS("Created demo user: demo / demo12345"))
        else:
            self.stdout.write("Demo user already exists.")

        # Sample topic
        topic, t_created = Topic.objects.get_or_create(
            user=user, name="Introduction to Machine Learning",
            defaults={'difficulty': 'medium', 'description': 'Sample topic for exploration.'},
        )
        if t_created:
            modules = _fallback_modules(topic.name, 5)
            for i, m in enumerate(modules):
                lm = LearningModule.objects.create(
                    topic=topic, order=i,
                    title=m['title'], content=m['content'],
                    key_points=m['key_points'], examples=m['examples'],
                    summary=m['summary'], reading_minutes=m['reading_minutes'],
                    is_unlocked=(i == 0),
                )
                for q in _fallback_mcqs(topic.name, 5):
                    ModuleQuestion.objects.create(
                        module=lm, question=q['question'], options=q['options'],
                        correct_index=q['correct_index'], explanation=q['explanation'],
                    )
            self.stdout.write(self.style.SUCCESS("Created sample topic with 5 modules."))
        else:
            self.stdout.write("Sample topic already exists.")

        self.stdout.write(self.style.SUCCESS("Done. Login at /accounts/login/ as demo / demo12345"))
