import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import InstantTest
from topics.models import Topic
from ai_engine.services import generate_unique_mcqs, generate_wrong_answer_explanation
from rewards.services import grant_points
from notifications.services import notify_test_completion
from analytics.services import record_analytics_snapshot, update_topic_difficulty


@login_required
def instant_index(request):
    topics = Topic.objects.filter(user=request.user)
    return render(request, 'exams/instant_index.html', {'topics': topics})


@login_required
def start_instant(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, user=request.user)
    today = timezone.now().date()
    # one attempt per day per topic
    existing_today = InstantTest.objects.filter(
        user=request.user, topic=topic, created_at__date=today
    ).first()
    if existing_today:
        if existing_today.completed:
            messages.info(request, "You've already attempted this instant test today. Try again tomorrow.")
            return redirect('exams:result', test_id=existing_today.id)
        return redirect('exams:take', test_id=existing_today.id)

    previous_questions = [
        q.get('question')
        for questions in InstantTest.objects.filter(user=request.user, topic=topic).values_list('questions', flat=True)
        for q in (questions or [])
        if q.get('question')
    ]
    mcqs = generate_unique_mcqs(
        topic.name,
        count=15,
        difficulty=topic.difficulty,
        purpose='instant',
        previous_questions=previous_questions,
    )
    random.shuffle(mcqs)
    test = InstantTest.objects.create(
        user=request.user, topic=topic,
        questions=mcqs, total_questions=len(mcqs),
    )
    return redirect('exams:take', test_id=test.id)


@login_required
def take_instant(request, test_id):
    test = get_object_or_404(InstantTest, id=test_id, user=request.user)
    if test.completed:
        return redirect('exams:result', test_id=test.id)

    if request.method == 'POST':
        answers = {}
        correct = 0
        review_items = []
        time_taken = int(request.POST.get('time_taken', 0) or 0)
        for i, q in enumerate(test.questions):
            ans_raw = request.POST.get(f'q_{i}')
            chosen_index = int(ans_raw) if ans_raw and ans_raw.isdigit() else -1
            answers[str(i)] = chosen_index
            is_correct = chosen_index == q['correct_index']
            if is_correct:
                correct += 1
            chosen_text = q['options'][chosen_index] if 0 <= chosen_index < 4 else "(no answer)"
            if not is_correct:
                ai_explain = generate_wrong_answer_explanation(
                    q['question'], chosen_text, q['options'][q['correct_index']], test.topic.name
                )
            else:
                ai_explain = q.get('explanation', '')
            review_items.append({
                'index': i, 'question': q['question'], 'options': q['options'],
                'correct_index': q['correct_index'], 'chosen_index': chosen_index,
                'is_correct': is_correct, 'explanation': ai_explain,
                'confusion_note': q.get('confusion_note', ''),
            })

        total = test.total_questions or 1
        score = round((correct / total) * 100, 2)
        test.answers = answers
        test.correct_count = correct
        test.score_percent = score
        test.time_taken_seconds = time_taken
        test.completed = True
        test.completed_at = timezone.now()
        test.save()
        update_topic_difficulty(test.topic, score)
        record_analytics_snapshot(request.user)

        passed = score >= 80
        if passed:
            grant_points(request.user, 15, reason="Instant test passed")
        try:
            notify_test_completion(request.user, f"Instant test: {test.topic.name}", score, passed)
        except Exception:
            pass
        # store review items in session so result page can display
        request.session[f'review_{test.id}'] = review_items
        return redirect('exams:result', test_id=test.id)

    return render(request, 'exams/instant_take.html', {'test': test})


@login_required
def instant_result(request, test_id):
    test = get_object_or_404(InstantTest, id=test_id, user=request.user)
    review_items = request.session.get(f'review_{test.id}', [])
    return render(request, 'exams/instant_result.html', {'test': test, 'review_items': review_items})


@login_required
def instant_history(request):
    tests = InstantTest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'exams/instant_history.html', {'tests': tests})
