from django.urls import path
from . import views

urlpatterns = [
    path('generate-questions/', views.generate_questions, name='generate_questions'),
    path('ask-question/', views.ask_question, name='ask_question'),
    path('test/', views.test_endpoint, name='test_endpoint'),
]
