from django.db import models
from django.contrib.auth.models import User
import uuid
import os


def upload_to(instance, filename):
    """Generate unique filename for uploaded files"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('cv_uploads', filename)


class CVGeneration(models.Model):
    """Model to store CV generation requests and results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    original_file = models.FileField(upload_to=upload_to, null=True, blank=True)
    original_text = models.TextField(blank=True)
    extra_notes = models.TextField(blank=True)
    generated_content = models.TextField(blank=True)
    word_file_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"CV Generation {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
