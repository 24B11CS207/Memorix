"""
AI service layer.
Handles Azure OpenAI calls for:
- Generating learning modules for a topic
- Generating MCQs (instant + review)
- Generating explanations for wrong answers
- Generating chatbot tutor responses
- Adaptive recommendations
"""
import json
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from openai import AzureOpenAI
    HAS_OPENAI = True
except Exception:
    HAS_OPENAI = False


def _client():
    if not HAS_OPENAI:
        return None
    if not (settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT):
        return None
    return AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    )


def _chat(messages, temperature=0.7, max_tokens=2000, retries=2, response_json=False):
    """Low-level chat call with retry handling. Returns text or None."""
    client = _client()
    if client is None:
        logger.warning("Azure OpenAI client not configured. Returning fallback content.")
        return None
    last_err = None
    for attempt in range(retries + 1):
        try:
            kwargs = dict(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if response_json:
                kwargs['response_format'] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            logger.exception("OpenAI call failed (attempt %s)", attempt + 1)
            time.sleep(1.5 * (attempt + 1))
    logger.error("All OpenAI attempts failed: %s", last_err)
    return None


# ----------------------- Prompt builders -----------------------

def _safe_json(text, fallback):
    """Extract JSON from a model response."""
    if not text:
        return fallback
    text = text.strip()
    # Try to strip markdown code fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    # Find first { and last }
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(text[start:end + 1])
    except Exception:
        pass
    return fallback


# ----------------------- Public API -----------------------

def generate_learning_modules(topic_name, difficulty='medium', num_modules=5):
    """Returns list of dicts: [{title, content, key_points[], examples[], reading_minutes}]."""
    system = (
        "You are an expert curriculum designer. You produce structured, accurate, "
        "step-by-step learning modules. Always respond in valid JSON."
    )
    user = f"""
Create {num_modules} learning modules for the topic: "{topic_name}" at {difficulty} difficulty.
Modules should progress from basic -> intermediate -> advanced.

Respond with this exact JSON structure:
{{
  "modules": [
    {{
      "title": "Module title",
      "content": "Full educational content (300-500 words, paragraphs)",
      "key_points": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"],
      "examples": ["short example 1", "short example 2"],
      "summary": "2-3 sentence summary",
      "reading_minutes": 5
    }}
  ]
}}
Only output JSON, no commentary.
"""
    text = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.6, max_tokens=3500, response_json=True,
    )
    data = _safe_json(text, {"modules": _fallback_modules(topic_name, num_modules)})
    return data.get("modules", _fallback_modules(topic_name, num_modules))


def generate_mcqs(topic_name, count=15, difficulty='medium', purpose='instant'):
    """Returns list of dicts: [{question, options[4], correct_index, explanation}]."""
    system = "You are an expert MCQ author. Always respond in valid JSON. Questions must be unambiguous and educational."
    user = f"""
Generate {count} multiple choice questions for the topic "{topic_name}" at {difficulty} difficulty.
Purpose: {purpose}

Each question must have exactly 4 options. Provide:
- a clear question
- 4 plausible options
- the index (0-3) of the correct option
- a concise explanation of why the correct answer is right
- a short note on why the wrong options can confuse learners (concept clarification)

Return strict JSON:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "...",
      "confusion_note": "..."
    }}
  ]
}}
"""
    text = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.5, max_tokens=4000, response_json=True,
    )
    data = _safe_json(text, {"questions": _fallback_mcqs(topic_name, count)})
    qs = data.get("questions", [])
    if not qs:
        qs = _fallback_mcqs(topic_name, count)
    # Validate shape
    cleaned = []
    for q in qs:
        try:
            assert len(q['options']) == 4
            assert 0 <= int(q['correct_index']) <= 3
            cleaned.append({
                'question': q['question'],
                'options': list(q['options']),
                'correct_index': int(q['correct_index']),
                'explanation': q.get('explanation', ''),
                'confusion_note': q.get('confusion_note', ''),
            })
        except Exception:
            continue
    if not cleaned:
        cleaned = _fallback_mcqs(topic_name, count)
    return cleaned[:count]


def generate_wrong_answer_explanation(question, chosen_option, correct_option, topic_name):
    """Personalized explanation when user answers wrong."""
    system = "You are a patient, supportive tutor. Be concise and clear."
    user = f"""
Topic: {topic_name}
Question: {question}
Student's answer: {chosen_option}
Correct answer: {correct_option}

Explain in 4-6 sentences:
1) Why the correct answer is right.
2) Why the student may have been confused.
3) A concept clarification.
4) A small improvement tip.
"""
    text = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.5, max_tokens=400,
    )
    return text or (
        f"The correct answer is '{correct_option}'. Review the core idea of {topic_name} and "
        f"compare it carefully with '{chosen_option}' to spot the distinction."
    )


def chatbot_reply(history, user_message, topic_context=None):
    """AI tutor chatbot."""
    system = (
        "You are DQMS Tutor — a friendly, accurate AI tutor. "
        "Use simple language, short paragraphs, and examples."
    )
    if topic_context:
        system += f" The student is currently studying: {topic_context}."
    msgs = [{"role": "system", "content": system}]
    for h in history[-10:]:
        msgs.append(h)
    msgs.append({"role": "user", "content": user_message})
    text = _chat(msgs, temperature=0.6, max_tokens=600)
    return text or "I'm having trouble reaching the AI service right now. Please try again shortly."


# ----------------------- Fallbacks (when API is unavailable) -----------------------

def _fallback_modules(topic, n):
    levels = ['Introduction', 'Core Concepts', 'Intermediate', 'Advanced', 'Mastery']
    out = []
    for i in range(n):
        level = levels[i] if i < len(levels) else f"Module {i+1}"
        out.append({
            'title': f"{topic} – {level}",
            'content': (
                f"This module covers {level.lower()} of {topic}. "
                f"It walks you through definitions, mechanisms, and practical reasoning. "
                f"Read carefully, then complete the mini-test to unlock the next module."
            ),
            'key_points': [
                f"Foundational idea of {topic}",
                f"Key terminology in {level}",
                f"Common pitfalls",
                f"How this connects to the next module",
            ],
            'examples': [f"Example illustrating {topic} basics", f"Practical scenario in {level}"],
            'summary': f"You learned {level.lower()} of {topic}. Take the mini-test to continue.",
            'reading_minutes': 5,
        })
    return out


def _fallback_mcqs(topic, n):
    out = []
    for i in range(n):
        out.append({
            'question': f"Sample question {i+1} about {topic}: which option best describes the core idea?",
            'options': [
                f"A correct conceptual statement about {topic}",
                f"A common misconception about {topic}",
                f"An unrelated statement",
                f"A partially correct but incomplete statement",
            ],
            'correct_index': 0,
            'explanation': f"Option 1 captures the central definition of {topic}.",
            'confusion_note': "Learners often pick option 2 because it sounds intuitive but it overgeneralizes.",
        })
    return out
