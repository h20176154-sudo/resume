from django.urls import path
from .views import GenerateCVView, ExportWordView

urlpatterns = [
    path('generate/', GenerateCVView.as_view(), name='generate_cv'),
    path('export/', ExportWordView.as_view(), name='export_word'),
]
