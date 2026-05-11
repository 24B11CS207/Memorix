import json
import logging
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .services import (
    chatbot_reply,
    memorix_generate_questions,
    memorix_generate_content,
    memorix_generate_mock,
)
from .models import AIUsageLog

logger = logging.getLogger(__name__)


# ── Memorix standalone-frontend API endpoints ─────────────────────
# These are CSRF-exempt because the HTML frontend uses localStorage auth,
# not Django session cookies. Rate limiting is handled by Gemini API quotas.

def _parse_body(request):
    try:
        return json.loads(request.body.decode()), None
    except Exception:
        return None, JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_POST
def api_tutor(request):
    """
    POST /ai/api/tutor/
    Body: {message, history[], topic, subject, class_name}
    Returns: {reply, source}
    """
    payload, err = _parse_body(request)
    if err:
        return err

    message = (payload.get('message') or '').strip()
    history = payload.get('history') or []
    topic = (payload.get('topic') or '').strip()
    subject = (payload.get('subject') or '').strip()
    class_name = (payload.get('class_name') or '').strip()

    if not message:
        return JsonResponse({'error': 'Message required'}, status=400)

    context_bits = [part for part in [class_name, subject, topic] if part]
    topic_context = " | ".join(context_bits) if context_bits else None

    try:
        reply = chatbot_reply(history, message, topic_context=topic_context)
        AIUsageLog.objects.create(kind='chat', note=message[:120])
        return JsonResponse({'reply': reply, 'source': 'ai'})
    except Exception as e:
        logger.warning('api_tutor error: %s', e)
        return JsonResponse({
            'reply': "I'm having trouble reaching the AI tutor right now. Please try again shortly.",
            'source': 'fallback',
            'error': str(e),
        }, status=200)


@csrf_exempt
@require_POST
def api_questions(request):
    """
    POST /ai/api/questions/
    Body: {topic, subject, class_name, module_index, count, history[], retry_hint}
    Returns: {questions: [...], source: 'gemini'|'static'}
    """
    payload, err = _parse_body(request)
    if err:
        return err

    topic        = (payload.get('topic') or '').strip()
    subject      = (payload.get('subject') or '').strip()
    class_name   = (payload.get('class_name') or '').strip()
    module_index = int(payload.get('module_index') or 0)
    count        = min(int(payload.get('count') or 10), 20)
    history      = payload.get('history') or []
    retry_hint   = bool(payload.get('retry_hint'))

    if not topic:
        return JsonResponse({'error': 'topic required'}, status=400)

    ai_error = ''
    try:
        questions = memorix_generate_questions(
            topic, subject, class_name, module_index, count, history, retry_hint
        )
        if questions:
            AIUsageLog.objects.create(kind='mcq', note=f'{class_name}|{subject}|{topic}|mod{module_index}'[:120])
            return JsonResponse({'questions': questions, 'source': 'gemini'})
    except Exception as e:
        ai_error = str(e)
        logger.warning('api_questions Gemini error: %s', e)

    if not ai_error:
        if settings.GEMINI_API_KEY:
            ai_error = 'Gemini returned no usable questions. Try again, or check the server log.'
        else:
            ai_error = 'No AI API key is loaded. Add GEMINI_API_KEY to .env and restart Django.'

    return JsonResponse({'questions': None, 'source': 'static', 'error': ai_error}, status=200)


@csrf_exempt
@require_POST
def api_content(request):
    """
    POST /ai/api/content/
    Body: {topic, subject, class_name, module_index}
    Returns: {explanation, key_points, examples, common_mistakes, summary, source}
    """
    payload, err = _parse_body(request)
    if err:
        return err

    topic        = (payload.get('topic') or '').strip()
    subject      = (payload.get('subject') or '').strip()
    class_name   = (payload.get('class_name') or '').strip()
    module_index = int(payload.get('module_index') or 0)

    if not topic:
        return JsonResponse({'error': 'topic required'}, status=400)

    try:
        content = memorix_generate_content(topic, subject, class_name, module_index)
        if content:
            AIUsageLog.objects.create(kind='modules', note=f'{class_name}|{subject}|{topic}|mod{module_index}'[:120])
            return JsonResponse({**content, 'source': 'gemini'})
    except Exception as e:
        logger.warning('api_content Gemini error: %s', e)

    return JsonResponse({'explanation': None, 'source': 'static'}, status=200)


@csrf_exempt
@require_POST
def api_mock(request):
    """
    POST /ai/api/mock/
    Body: {topic, subject, class_name, completed_modules, attempt_num, count, history[], retry_hint}
    Returns: {questions: [...], source: 'gemini'|'static'}
    """
    payload, err = _parse_body(request)
    if err:
        return err

    topic             = (payload.get('topic') or '').strip()
    subject           = (payload.get('subject') or '').strip()
    class_name        = (payload.get('class_name') or '').strip()
    completed_modules = int(payload.get('completed_modules') or 1)
    attempt_num       = int(payload.get('attempt_num') or 1)
    count             = min(int(payload.get('count') or 10), 20)
    history           = payload.get('history') or []
    retry_hint        = bool(payload.get('retry_hint'))

    if not topic:
        return JsonResponse({'error': 'topic required'}, status=400)

    ai_error = ''
    try:
        questions = memorix_generate_mock(
            topic, subject, class_name, completed_modules,
            attempt_num, count, history, retry_hint
        )
        if questions:
            AIUsageLog.objects.create(kind='mcq', note=f'mock|{class_name}|{subject}|{topic}|att{attempt_num}'[:120])
            return JsonResponse({'questions': questions, 'source': 'gemini'})
    except Exception as e:
        ai_error = str(e)
        logger.warning('api_mock Gemini error: %s', e)

    if not ai_error:
        if settings.GEMINI_API_KEY:
            ai_error = 'Gemini returned no usable mock questions. Try again, or check the server log.'
        else:
            ai_error = 'No AI API key is loaded. Add GEMINI_API_KEY to .env and restart Django.'

    return JsonResponse({'questions': None, 'source': 'static', 'error': ai_error}, status=200)


# ── Django-session authenticated views ────────────────────────────

@login_required
def chatbot_page(request):
    return render(request, 'ai_engine/chatbot.html')


@login_required
@require_POST
def chatbot_api(request):
    try:
        payload = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    history = payload.get('history', [])
    message = (payload.get('message') or '').strip()
    topic_context = payload.get('topic') or None
    if not message:
        return JsonResponse({'error': 'Message required'}, status=400)

    reply = chatbot_reply(history, message, topic_context=topic_context)
    AIUsageLog.objects.create(user=request.user, kind='chat', note=message[:120])
    return JsonResponse({'reply': reply})
