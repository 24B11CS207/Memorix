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
import requests

logger = logging.getLogger(__name__)

try:
    from openai import AzureOpenAI, OpenAI
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


def _grok_client():
    if not HAS_OPENAI:
        return None
    if not settings.XAI_API_KEY:
        return None
    return OpenAI(
        api_key=settings.XAI_API_KEY,
        base_url=settings.XAI_BASE_URL,
        timeout=45,
    )


def _gemini_chat(messages, temperature=0.7, max_tokens=2000, response_json=False):
    if not settings.GEMINI_API_KEY:
        return None

    prompt_parts = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        prompt_parts.append(f"{role.upper()}:\n{content}")
    prompt = "\n\n".join(prompt_parts)

    generation_config = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
    }
    if response_json:
        generation_config["responseMimeType"] = "application/json"

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }

    try:
        response = requests.post(
            url,
            params={"key": settings.GEMINI_API_KEY},
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        raise RuntimeError("Gemini API request failed") from exc
    if response.status_code >= 400:
        raise RuntimeError(f"Gemini API HTTP {response.status_code}")
    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        return None
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(part.get("text", "") for part in parts).strip() or None


def _grok_chat(messages, temperature=0.7, max_tokens=2000, response_json=False):
    client = _grok_client()
    if client is None:
        return None

    kwargs = dict(
        model=settings.XAI_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if response_json:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def _chat(messages, temperature=0.7, max_tokens=2000, retries=2, response_json=False):
    """Low-level chat call with retry handling. Returns text or None."""
    if settings.GEMINI_API_KEY:
        last_err = None
        for attempt in range(retries + 1):
            try:
                return _gemini_chat(messages, temperature, max_tokens, response_json)
            except Exception as e:
                last_err = e
                logger.warning("Gemini call failed (attempt %s): %s", attempt + 1, e)
            time.sleep(1.5 * (attempt + 1))
        logger.error("All Gemini attempts failed: %s", last_err)

    if settings.XAI_API_KEY:
        last_err = None
        for attempt in range(retries + 1):
            try:
                return _grok_chat(messages, temperature, max_tokens, response_json)
            except Exception as e:
                last_err = e
                logger.warning("Grok call failed (attempt %s): %s", attempt + 1, e)
                time.sleep(1.5 * (attempt + 1))
        logger.error("All Grok attempts failed: %s", last_err)

    client = _client()
    if client is None:
        logger.warning("No AI provider configured. Returning fallback content.")
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


def generate_topic_explanation(topic_name, difficulty='medium', context=''):
    """Generate a concise topic overview for the topic detail page."""
    system = (
        "You are an expert tutor. Explain topics clearly for students. "
        "Keep the explanation accurate, structured, and practical."
    )
    user = f"""
Write a helpful explanation for the topic "{topic_name}" at {difficulty} difficulty.
Additional context: {context or "None"}

Return 3 short paragraphs:
1) what the topic means,
2) why it matters,
3) how the student should start learning it.
"""
    text = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.55, max_tokens=700,
    )
    return text or (
        f"{topic_name} is an important topic to study step by step. Start by learning the "
        "basic definition, then connect the key concepts with examples and practice questions. "
        "After that, revise the weak areas and test yourself to improve retention."
    )


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


def _normalize_question_text(text):
    return " ".join((text or "").lower().strip().split())


def generate_unique_mcqs(topic_name, count=15, difficulty='medium', purpose='instant', previous_questions=None):
    """
    Generate MCQs while filtering out repeated question text.
    The caller supplies historical questions from database/session context.
    """
    seen = {_normalize_question_text(q) for q in (previous_questions or []) if q}
    unique = []
    attempts = 0

    while len(unique) < count and attempts < 3:
        needed = count - len(unique)
        avoid_list = list(seen)[:40]
        avoid_note = ""
        if avoid_list:
            avoid_note = " Avoid repeating these earlier questions: " + " | ".join(avoid_list[:12])
        generated = generate_mcqs(
            topic_name,
            count=max(needed * 2, needed),
            difficulty=difficulty,
            purpose=f"{purpose}. Create new non-repeated questions.{avoid_note}",
        )
        for question in generated:
            normalized = _normalize_question_text(question.get('question'))
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(question)
            if len(unique) == count:
                break
        attempts += 1

    if len(unique) < count:
        for question in _fallback_mcqs(topic_name, count * 2):
            normalized = _normalize_question_text(question.get('question'))
            if normalized in seen:
                continue
            seen.add(normalized)
            unique.append(question)
            if len(unique) == count:
                break

    return unique[:count]


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


# ─────────────────────────────────────────────────────────────────
#  MEMORIX STANDALONE FRONTEND — dedicated Gemini service functions
#  Called by /ai/api/questions/, /ai/api/content/, /ai/api/mock/
# ─────────────────────────────────────────────────────────────────

_MODULE_FOCUS = [
    "basic definitions, keywords, and the simplest introduction to the topic",
    "core rules, formulas, key mechanisms, and the main theory behind the topic",
    "solved examples, step-by-step worked problems, and common question patterns",
    "application-level and exam-style questions that mix concepts and require multi-step reasoning",
    "final revision: a comprehensive review of all aspects, common errors, and exam readiness tips",
]

_CLASS_STYLE = {
    "child": (
        "extremely simple language suitable for ages 6-10. Use short sentences, "
        "colourful real-life examples (fruits, toys, animals, shapes), emoji-friendly descriptions, "
        "and avoid any technical jargon."
    ),
    "school": (
        "clear, straightforward language for school students (grades 6-10). "
        "Use relatable examples from daily life, textbook-style explanations, and moderate vocabulary."
    ),
    "intermediate": (
        "academic language for Intermediate/11-12 level students. "
        "Include formulas where relevant, precise definitions, and board-exam style questions."
    ),
    "advanced": (
        "technical, university-level language. Include precise terminology, derivations where applicable, "
        "and professional/competitive-exam style questions."
    ),
}


def _class_level(class_name):
    """Map a class/path string to a difficulty tier."""
    lower = (class_name or "").lower()
    for n in ["class 1", "class 2", "class 3", "class 4", "class 5",
              "1st", "2nd", "3rd", "4th", "5th"]:
        if n in lower:
            return "child"
    for n in ["class 6", "class 7", "class 8", "class 9", "class 10",
              "6th", "7th", "8th", "9th", "10th"]:
        if n in lower:
            return "school"
    if "intermediate" in lower:
        return "intermediate"
    return "advanced"


def memorix_generate_questions(topic, subject, class_name, module_index, count, history, retry_hint=False):
    """
    Generate topic-specific, module-aware MCQs for the Memorix frontend.
    Returns list of {question, options[4], correct_index, explanation, concept}.
    history — list of previous question texts for deduplication.
    """
    level  = _class_level(class_name)
    style  = _CLASS_STYLE.get(level, _CLASS_STYLE["school"])
    focus  = _MODULE_FOCUS[module_index] if 0 <= module_index < len(_MODULE_FOCUS) else _MODULE_FOCUS[0]
    avoid  = ""
    if history:
        sample = " | ".join(str(h)[:90] for h in history[:20])
        avoid = f"\n\nDo NOT generate any of these already-seen questions or close paraphrases:\n{sample}"
    retry_note = " Make questions distinctly different from any previous batch." if retry_hint else ""

    system = (
        "You are an expert educational question designer for the Memorix AI learning platform. "
        "Always respond with ONLY valid JSON, no prose, no markdown fences."
    )
    user = f"""
Generate exactly {count} multiple-choice questions for:
- Class / Path: {class_name}
- Subject: {subject}
- Topic: {topic}
- Module focus: {focus}

Language style: {style}

STRICT RULES:
1. Every question MUST be directly about "{topic}" in the context of "{subject}".
2. Do NOT include questions about unrelated topics.
3. Each question must have exactly 4 options.
4. Vary question types: definition, application, numerical, conceptual, fill-in-the-blank style, real-life scenario.
5. For child-level: use objects, cartoons, colours, fruits, animals as examples.
6. correct_index is the 0-based index of the correct option.{avoid}{retry_note}

Return this exact JSON:
{{
  "questions": [
    {{
      "question": "question text",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "why this answer is correct and why the others are wrong",
      "concept": "short concept label (2-5 words)"
    }}
  ]
}}
"""
    text = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.62, max_tokens=4500, response_json=True,
    )
    data = _safe_json(text, {})
    questions = data.get("questions", [])
    cleaned = []
    for q in questions:
        try:
            opts = list(q["options"])
            assert len(opts) == 4
            ci = int(q["correct_index"])
            assert 0 <= ci <= 3
            cleaned.append({
                "question":      str(q["question"]),
                "options":       opts,
                "correct_index": ci,
                "explanation":   str(q.get("explanation", "")),
                "concept":       str(q.get("concept", topic)),
            })
        except Exception:
            continue
    return cleaned[:count]


def memorix_generate_content(topic, subject, class_name, module_index):
    """
    Generate rich learning content for a single Memorix module.
    Returns {explanation, key_points, examples, common_mistakes, summary}.
    """
    level = _class_level(class_name)
    style = _CLASS_STYLE.get(level, _CLASS_STYLE["school"])
    focus = _MODULE_FOCUS[module_index] if 0 <= module_index < len(_MODULE_FOCUS) else _MODULE_FOCUS[0]

    system = (
        "You are an expert curriculum author for the Memorix AI learning platform. "
        "Always respond with ONLY valid JSON, no markdown fences."
    )
    user = f"""
Create a complete learning module for:
- Class / Path: {class_name}
- Subject: {subject}
- Topic: {topic}
- Module focus: {focus}

Language style: {style}

Return ONLY this JSON:
{{
  "explanation": "Full, clear, structured explanation (4-8 paragraphs separated by \\n\\n). Make it educational and engaging.",
  "key_points": ["key point 1", "key point 2", "key point 3", "key point 4", "key point 5"],
  "examples": [
    "Example 1 — describe fully in 1-2 sentences",
    "Example 2 — describe fully in 1-2 sentences",
    "Example 3 — describe fully in 1-2 sentences"
  ],
  "common_mistakes": [
    "Mistake 1 students commonly make",
    "Mistake 2 students commonly make",
    "Mistake 3 students commonly make"
  ],
  "summary": "A 2-3 sentence revision summary of this module."
}}

Rules:
- For child-level: use simple words, fun real-life examples (pizza, chocolate, toys, animals).
- For advanced: use precise terminology and include formulas or derivations where relevant.
- Keep content focused strictly on "{topic}" within "{subject}".
"""
    text = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.55, max_tokens=3000, response_json=True,
    )
    data = _safe_json(text, {})
    if not data.get("explanation"):
        return None
    return {
        "explanation":     str(data.get("explanation", "")),
        "key_points":      [str(p) for p in data.get("key_points", [])],
        "examples":        [str(e) for e in data.get("examples", [])],
        "common_mistakes": [str(m) for m in data.get("common_mistakes", [])],
        "summary":         str(data.get("summary", "")),
    }


def memorix_generate_mock(topic, subject, class_name, completed_modules, attempt_num, count, history, retry_hint=False):
    """
    Generate a comprehensive mock test covering all completed modules.
    Returns list of {question, options[4], correct_index, explanation, concept}.
    """
    level     = _class_level(class_name)
    style     = _CLASS_STYLE.get(level, _CLASS_STYLE["school"])
    mod_names = [_MODULE_FOCUS[i] for i in range(min(completed_modules, len(_MODULE_FOCUS)))]
    coverage  = "; ".join(mod_names) if mod_names else "all aspects of the topic"
    avoid     = ""
    if history:
        sample = " | ".join(str(h)[:90] for h in history[:20])
        avoid = f"\n\nDo NOT repeat or closely paraphrase these earlier mock questions:\n{sample}"
    retry_note = " Generate distinctly different questions from any previous mock attempt." if retry_hint else ""

    system = (
        "You are an expert exam question designer for the Memorix AI platform. "
        "Always respond with ONLY valid JSON, no markdown fences."
    )
    user = f"""
Generate exactly {count} mock test questions (attempt #{attempt_num}) for:
- Class / Path: {class_name}
- Subject: {subject}
- Topic: {topic}
- Modules covered: {completed_modules} modules ({coverage})

Language style: {style}

RULES:
1. All questions must be about "{topic}" in "{subject}".
2. Cover the full breadth of completed modules — mix easy, medium, and hard.
3. Include definition, application, reasoning, and case-based question types.
4. Each question has exactly 4 options.
5. correct_index is 0-based.{avoid}{retry_note}

Return ONLY this JSON:
{{
  "questions": [
    {{
      "question": "question text",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "clear explanation of the correct answer",
      "concept": "concept label (2-5 words)"
    }}
  ]
}}
"""
    text = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.65, max_tokens=4500, response_json=True,
    )
    data = _safe_json(text, {})
    questions = data.get("questions", [])
    cleaned = []
    for q in questions:
        try:
            opts = list(q["options"])
            assert len(opts) == 4
            ci = int(q["correct_index"])
            assert 0 <= ci <= 3
            cleaned.append({
                "question":      str(q["question"]),
                "options":       opts,
                "correct_index": ci,
                "explanation":   str(q.get("explanation", "")),
                "concept":       str(q.get("concept", topic)),
            })
        except Exception:
            continue
    return cleaned[:count]
