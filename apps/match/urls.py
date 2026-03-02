from django.urls import path
from .views import MatchJobDescriptionView, BatchJobMatchingView

urlpatterns = [
    path('match-job-description/', MatchJobDescriptionView.as_view(), name='match-job-description'),
    path('batch-match-jobs/', BatchJobMatchingView.as_view(), name='batch-match-jobs'),
]
