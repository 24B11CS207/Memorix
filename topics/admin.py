from django.contrib import admin
from .models import Topic, LearningModule, ModuleQuestion, ModuleAttempt


class LearningModuleInline(admin.TabularInline):
    model = LearningModule
    extra = 0


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'difficulty', 'is_completed', 'accuracy_percent', 'created_at')
    list_filter = ('difficulty', 'is_completed')
    search_fields = ('name', 'user__username')
    inlines = [LearningModuleInline]


@admin.register(LearningModule)
class LearningModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'order', 'is_unlocked', 'is_completed')
    list_filter = ('is_completed', 'is_unlocked')


@admin.register(ModuleQuestion)
class ModuleQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'module', 'correct_index')


@admin.register(ModuleAttempt)
class ModuleAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'score_percent', 'passed', 'attempted_at')
    list_filter = ('passed',)
