from django.test import TestCase
from .models import CVGeneration


class CVGenerationModelTest(TestCase):
    def test_cv_generation_creation(self):
        cv = CVGeneration.objects.create(
            original_text="Test resume text",
            extra_notes="Additional notes",
            generated_content="Generated CV content"
        )
        self.assertEqual(cv.original_text, "Test resume text")
        self.assertEqual(cv.extra_notes, "Additional notes")
        self.assertEqual(cv.generated_content, "Generated CV content")
