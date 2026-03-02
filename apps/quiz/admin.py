from django.contrib import admin
from .models import QuizSession, QuizScore


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'language', 'question_count', 'user', 'created_at']


@admin.register(QuizScore)
class QuizScoreAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'quiz_session', 'score', 'total', 'created_at']
