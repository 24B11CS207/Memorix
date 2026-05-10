import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .services import chatbot_reply
from .models import AIUsageLog


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
