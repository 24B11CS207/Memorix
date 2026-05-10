from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import RevisionPlan, ReviewSession, REVIEW_SCHEDULES
from topics.models import Topic
from ai_engine.services import generate_mcqs, generate_wrong_answer_explanation
from rewards.services import grant_points
from notifications.services import notify_test_completion


@login_required
def revisions_index(request):
    plans = RevisionPlan.objects.filter(user=request.user).select_related('topic')
    topics = Topic.objects.filter(user=request.user)
    today = timezone.now().date()
    due_sessions = ReviewSession.objects.filter(
        plan__user=request.user, scheduled_date__lte=today,
    ).exclude(status='passed').select_related('plan__topic').order_by('scheduled_date')
    return render(request, 'revisions/index.html', {
        'plans': plans, 'topics': topics,
        'due_sessions': due_sessions,
        'review_options': [4, 5, 6],
    })


@login_required
def create_plan(request):
    if request.method == 'POST':
        topic_id = request.POST.get('topic_id')
        try:
            total = int(request.POST.get('total_reviews', 4))
        except ValueError:
            total = 4
        if total not in REVIEW_SCHEDULES:
            messages.error(request, "Invalid review count.")
            return redirect('revisions:index')
        topic = get_object_or_404(Topic, id=topic_id, user=request.user)
        # Avoid duplicate active plan
        existing = RevisionPlan.objects.filter(user=request.user, topic=topic, is_completed=False).first()
        if existing:
            messages.info(request, "An active plan already exists for this topic.")
            return redirect('revisions:plan_detail', plan_id=existing.id)
        plan = RevisionPlan.create_with_schedule(request.user, topic, total)
        messages.success(request, f"{total}-review plan created for '{topic.name}'.")
        return redirect('revisions:plan_detail', plan_id=plan.id)
    return redirect('revisions:index')


@login_required
def plan_detail(request, plan_id):
    plan = get_object_or_404(RevisionPlan, id=plan_id, user=request.user)
    sessions = plan.sessions.all()
    return render(request, 'revisions/plan_detail.html', {'plan': plan, 'sessions': sessions})


@login_required
def take_review(request, session_id):
    session = get_object_or_404(ReviewSession, id=session_id, plan__user=request.user)
    plan = session.plan
    today = timezone.now().date()

    if session.status == 'passed':
        messages.info(request, "This review is already passed.")
        return redirect('revisions:plan_detail', plan_id=plan.id)
    if session.scheduled_date > today:
        messages.warning(request, f"This review is scheduled for {session.scheduled_date}.")
        return redirect('revisions:plan_detail', plan_id=plan.id)

    # Block if previous review not passed
    prev = ReviewSession.objects.filter(
        plan=plan, review_number__lt=session.review_number
    ).exclude(status='passed').first()
    if prev:
        messages.warning(request, f"Pass review #{prev.review_number} first.")
        return redirect('revisions:plan_detail', plan_id=plan.id)

    # Generate MCQs only on first load if not present
    if not session.questions:
        session.questions = generate_mcqs(
            plan.topic.name, count=15, difficulty=plan.topic.difficulty,
            purpose=f'review_{session.review_number}'
        )
        session.status = 'available'
        session.save()

    if request.method == 'POST':
        answers = {}
        correct = 0
        review_items = []
        for i, q in enumerate(session.questions):
            ans_raw = request.POST.get(f'q_{i}')
            ci = int(ans_raw) if ans_raw and ans_raw.isdigit() else -1
            answers[str(i)] = ci
            is_correct = ci == q['correct_index']
            if is_correct:
                correct += 1
            chosen_text = q['options'][ci] if 0 <= ci < 4 else "(no answer)"
            if not is_correct:
                ai_explain = generate_wrong_answer_explanation(
                    q['question'], chosen_text, q['options'][q['correct_index']], plan.topic.name
                )
            else:
                ai_explain = q.get('explanation', '')
            review_items.append({
                'index': i, 'question': q['question'], 'options': q['options'],
                'correct_index': q['correct_index'], 'chosen_index': ci,
                'is_correct': is_correct, 'explanation': ai_explain,
                'confusion_note': q.get('confusion_note', ''),
            })

        total = len(session.questions) or 1
        score = round((correct / total) * 100, 2)
        passed = score >= 80
        session.answers = answers
        session.score_percent = score
        session.attempts += 1
        session.completed_at = timezone.now()
        session.status = 'passed' if passed else 'failed'
        session.save()

        if passed:
            grant_points(request.user, 5, reason="Review completed")
            # if all sessions of plan are passed -> mark plan completed
            if not plan.sessions.exclude(status='passed').exists():
                plan.is_completed = True
                plan.save(update_fields=['is_completed'])
        else:
            # shift later sessions by 1 day
            session.shift_future_sessions(days=1)

        try:
            notify_test_completion(
                request.user, f"Review #{session.review_number}: {plan.topic.name}", score, passed
            )
        except Exception:
            pass

        request.session[f'rev_review_{session.id}'] = review_items
        return redirect('revisions:result', session_id=session.id)

    return render(request, 'revisions/take_review.html', {'session': session, 'plan': plan})


@login_required
def review_result(request, session_id):
    session = get_object_or_404(ReviewSession, id=session_id, plan__user=request.user)
    review_items = request.session.get(f'rev_review_{session.id}', [])
    return render(request, 'revisions/review_result.html', {'session': session, 'review_items': review_items})
