from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_quiz),
    path('submit/', views.submit_quiz),
    path('history/', views.quiz_history),
]
