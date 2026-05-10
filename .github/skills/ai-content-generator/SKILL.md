---
name: ai-content-generator
description: "Use when: generating AI-powered learning modules, questions, and content for topics in the DQMS educational platform. Automates the workflow from topic input to AI-generated modules with mini-tests."
---

# AI Content Generator Skill

## Purpose
This skill automates the creation of AI-generated learning content for the DQMS platform. It takes a topic input, generates structured learning modules with key points, explanations, and multiple-choice questions using Azure OpenAI, and saves them to the database.

## Workflow
1. **Topic Input**: Accept or create a new Topic model instance with the provided topic name.
2. **Module Generation**: Use `ai_engine.services.generate_learning_module()` to create 5 progressive modules per topic.
3. **Question Creation**: Generate mini-test questions for each module using AI.
4. **Database Save**: Persist the generated content to Topic, LearningModule, and ModuleQuestion models.
5. **Validation**: Ensure content is saved correctly and handle AI fallbacks if OpenAI is unavailable.

## Guidelines
- Always route AI calls through `ai_engine/services.py` for consistency and error handling.
- Follow the project's JSONField patterns for flexible data storage.
- If AI fails, use static fallback content as per conventions.
- Update model relationships correctly (e.g., Topic.modules, Module.questions).
- Run migrations if needed before saving.

## Assets
- No bundled scripts/templates needed; uses existing Django models and AI services.
- Example: For topic "Machine Learning", generates modules on basics, algorithms, etc., with 10 MCQs each.

## Usage
Invoke this skill when adding new topics or regenerating content. It ensures AI integration follows project patterns.