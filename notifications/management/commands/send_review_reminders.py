from django.core.management.base import BaseCommand
from django.utils import timezone
from revisions.models import ReviewSession
from notifications.services import notify_review_due


class Command(BaseCommand):
    help = "Send email reminders for review sessions due today."

    def handle(self, *args, **options):
        today = timezone.now().date()
        due = ReviewSession.objects.filter(
            scheduled_date=today
        ).exclude(status='passed').select_related('plan__user', 'plan__topic')

        sent = 0
        for s in due:
            try:
                notify_review_due(s.plan.user, s.plan.topic.name, s.review_number)
                sent += 1
            except Exception as e:
                self.stderr.write(f"Failed for {s}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Sent {sent} review reminders."))
