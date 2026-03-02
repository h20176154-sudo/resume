from django.db import models
from django.contrib.auth.models import User


class QuizSession(models.Model):
    """Stores a generated quiz with its questions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='quiz_sessions')
    language = models.CharField(max_length=100)
    question_count = models.IntegerField()
    questions = models.JSONField()  # [{"question": "...", "options": ["A","B","C","D"], "answer": "A"}]
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz {self.language} - {self.question_count} questions"


class QuizScore(models.Model):
    """Stores user quiz scores."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='quiz_scores')
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='scores')
    score = models.IntegerField()
    total = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Score {self.score}/{self.total}"
