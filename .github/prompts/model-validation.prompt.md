---
name: model-validation
description: "Use when: validating Django model definitions, relationships, and database schema for the DQMS project. Checks for proper fields, constraints, and migrations."
---

# Django Model Validation Prompt

## Task
Analyze the provided Django model file(s) in the DQMS project. Validate:

- Field definitions (types, null/blank settings, defaults)
- Relationships (ForeignKey, ManyToMany, OneToOne) and their on_delete behaviors
- Model methods and properties
- Meta class options (ordering, unique_together, etc.)
- JSONField usage for flexible data
- Consistency with project conventions (e.g., JSONField for questions/options)

## Output
Provide a validation report with:
- Any issues or improvements needed
- Migration implications
- Suggestions for better practices
- Confirmation if the model follows DQMS patterns

## Guidelines
- Reference AGENTS.md for project conventions
- Suggest fixes if problems are found
- Focus on database integrity and performance
- Check for potential data migration issues

## Parameters
- model_file: Path to the model file to validate (e.g., topics/models.py)