import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, View
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .models import Topic, LearningModule, ModuleQuestion, ModuleAttempt
from .forms import TopicForm
from ai_engine.services import generate_learning_modules, generate_mcqs, generate_wrong_answer_explanation
from rewards.services import grant_topic_completion_rewards
from notifications.services import notify_test_completion


def _shuffle_module_quiz_options(question):
    correct_option = question['options'][question['correct_index']]
    options = list(question['options'])
    random.shuffle(options)
    question['options'] = options
    question['correct_index'] = options.index(correct_option)
    return question


def _module_question_to_dict(question, index):
    return {
        'id': index,
        'question': question.question,
        'options': list(question.options),
        'correct_index': question.correct_index,
        'explanation': question.explanation,
    }


def _fresh_module_quiz_questions(topic, module, count=5):
    generated = generate_mcqs(
        f"{topic.name} - {module.title}",
        count=count,
        difficulty=topic.difficulty,
        purpose=f"module_quiz_fresh_attempt_{random.randint(1000, 999999)}",
    )
    questions = []
    for index, question in enumerate(generated):
        if len(question.get('options', [])) == 4:
            questions.append({
                'id': index,
                'question': question['question'],
                'options': list(question['options']),
                'correct_index': int(question['correct_index']),
                'explanation': question.get('explanation', ''),
            })

    if len(questions) < count:
        existing = list(module.questions.all())
        random.shuffle(existing)
        start_index = len(questions)
        for offset, question in enumerate(existing[:count - len(questions)]):
            questions.append(_module_question_to_dict(question, start_index + offset))

    questions = [_shuffle_module_quiz_options(question) for question in questions[:count]]
    random.shuffle(questions)
    for index, question in enumerate(questions):
        question['id'] = index
    return questions


class TopicListView(LoginRequiredMixin, ListView):
    template_name = 'topics/topic_list.html'
    context_object_name = 'topics'
    paginate_by = 12

    def get_queryset(self):
        qs = Topic.objects.filter(user=self.request.user)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        diff = self.request.GET.get('difficulty')
        if diff in ('easy', 'medium', 'hard'):
            qs = qs.filter(difficulty=diff)
        return qs


class TopicCreateView(LoginRequiredMixin, CreateView):
    """Create a topic AND auto-generate AI learning modules + mini-test questions."""
    model = Topic
    form_class = TopicForm
    template_name = 'topics/topic_form.html'

    def get_initial(self):
        initial = super().get_initial()
        name = self.request.GET.get('name')
        description = self.request.GET.get('description')
        difficulty = self.request.GET.get('difficulty')
        if name:
            initial['name'] = name[:200]
        if description:
            initial['description'] = description
        if difficulty in ('easy', 'medium', 'hard'):
            initial['difficulty'] = difficulty
        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        topic = self.object
        # Generate modules via AI
        modules_data = generate_learning_modules(topic.name, topic.difficulty, num_modules=5)
        for i, m in enumerate(modules_data):
            lm = LearningModule.objects.create(
                topic=topic,
                order=i,
                title=m.get('title', f"Module {i+1}"),
                content=m.get('content', ''),
                key_points=m.get('key_points', []),
                examples=m.get('examples', []),
                summary=m.get('summary', ''),
                reading_minutes=m.get('reading_minutes', 5),
                is_unlocked=(i == 0),  # only first unlocked
            )
            # Generate 5 mini-test questions for the module
            mcqs = generate_mcqs(f"{topic.name} - {lm.title}", count=5, difficulty=topic.difficulty, purpose='module_quiz')
            for q in mcqs:
                ModuleQuestion.objects.create(
                    module=lm,
                    question=q['question'],
                    options=q['options'],
                    correct_index=q['correct_index'],
                    explanation=q.get('explanation', ''),
                )
        messages.success(self.request, f"Topic '{topic.name}' created with AI-generated modules.")
        return response

    def get_success_url(self):
        return reverse('topics:detail', kwargs={'pk': self.object.pk})


class TopicDetailView(LoginRequiredMixin, DetailView):
    model = Topic
    template_name = 'topics/topic_detail.html'
    context_object_name = 'topic'

    def get_queryset(self):
        return Topic.objects.filter(user=self.request.user)


@login_required
def module_view(request, topic_id, module_id):
    topic = get_object_or_404(Topic, id=topic_id, user=request.user)
    module = get_object_or_404(LearningModule, id=module_id, topic=topic)
    if not module.is_unlocked:
        messages.warning(request, "Complete the previous module first.")
        return redirect('topics:detail', pk=topic.id)
    return render(request, 'topics/module_detail.html', {'topic': topic, 'module': module})


@login_required
def module_quiz(request, topic_id, module_id):
    topic = get_object_or_404(Topic, id=topic_id, user=request.user)
    module = get_object_or_404(LearningModule, id=module_id, topic=topic)
    if not module.is_unlocked:
        return redirect('topics:detail', pk=topic.id)

    session_key = f'module_quiz_questions_{module.id}'

    if request.method == 'POST':
        questions = request.session.get(session_key) or _fresh_module_quiz_questions(topic, module)
        correct_count = 0
        review_items = []
        for q in questions:
            chosen = request.POST.get(f"q_{q['id']}")
            is_correct = False
            chosen_text = ''
            if chosen is not None and chosen.isdigit():
                ci = int(chosen)
                if 0 <= ci < len(q['options']):
                    chosen_text = q['options'][ci]
                    if ci == q['correct_index']:
                        is_correct = True
                        correct_count += 1
            if not is_correct:
                explanation = generate_wrong_answer_explanation(
                    q['question'], chosen_text or "(no answer)", q['options'][q['correct_index']], topic.name
                )
            else:
                explanation = q.get('explanation', '')
            review_items.append({
                'question': q,
                'chosen_text': chosen_text,
                'is_correct': is_correct,
                'correct_text': q['options'][q['correct_index']],
                'explanation': explanation,
            })

        total = len(questions) or 1
        score = round((correct_count / total) * 100, 2)
        passed = score >= 80
        ModuleAttempt.objects.create(user=request.user, module=module, score_percent=score, passed=passed)

        if passed and not module.is_completed:
            module.is_completed = True
            module.save(update_fields=['is_completed'])
            # unlock next module
            next_mod = LearningModule.objects.filter(topic=topic, order=module.order + 1).first()
            if next_mod and not next_mod.is_unlocked:
                next_mod.is_unlocked = True
                next_mod.save(update_fields=['is_unlocked'])
            # if all modules done -> mark topic completed and grant rewards
            if topic.modules.filter(is_completed=True).count() == topic.modules.count():
                topic.is_completed = True
                topic.save(update_fields=['is_completed'])
                grant_topic_completion_rewards(request.user)

        try:
            notify_test_completion(request.user, f"Module quiz: {module.title}", score, passed)
        except Exception:
            pass

        request.session.pop(session_key, None)
        return render(request, 'topics/module_quiz_result.html', {
            'topic': topic, 'module': module,
            'score': score, 'passed': passed,
            'review_items': review_items,
        })

    questions = _fresh_module_quiz_questions(topic, module)
    request.session[session_key] = questions
    request.session.modified = True
    return render(request, 'topics/module_quiz.html', {'topic': topic, 'module': module, 'questions': questions})


@login_required
def topic_delete(request, pk):
    topic = get_object_or_404(Topic, pk=pk, user=request.user)
    if request.method == 'POST':
        topic.delete()
        messages.success(request, "Topic deleted.")
        return redirect('topics:list')
    return render(request, 'topics/topic_confirm_delete.html', {'topic': topic})
