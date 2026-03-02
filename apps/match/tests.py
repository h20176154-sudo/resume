from django.test import TestCase
from django.contrib.auth.models import User
from users.models import Profile
from .matching import (
    extract_skills_from_text,
    extract_experience_years,
    extract_education_level,
    categorize_skills,
    extract_soft_skills,
    calculate_skill_match_score,
    calculate_experience_match,
    calculate_education_match,
    calculate_match_score
)


class SkillExtractionTests(TestCase):
    """Test skill extraction from text."""
    
    def test_single_word_skills(self):
        """Test extraction of single-word skills."""
        text = "Python, Java, JavaScript developer with SQL expertise"
        skills = extract_skills_from_text(text)
        self.assertIn("python", skills)
        self.assertIn("java", skills)
        self.assertIn("javascript", skills)
        self.assertIn("sql", skills)
    
    def test_multi_word_skills(self):
        """Test extraction of multi-word skills."""
        text = "machine learning and natural language processing expert"
        skills = extract_skills_from_text(text)
        self.assertIn("machine learning", skills)
        self.assertIn("natural language processing", skills)


class ExperienceExtractionTests(TestCase):
    """Test experience extraction from text."""
    
    def test_years_extraction(self):
        """Test extraction of years from experience text."""
        text = "5 years of experience in software development"
        years = extract_experience_years(text)
        self.assertEqual(years, 5)
    
    def test_years_with_plus(self):
        """Test extraction of years with + notation."""
        text = "8+ years as a senior engineer"
        years = extract_experience_years(text)
        self.assertEqual(years, 8)


class EducationExtractionTests(TestCase):
    """Test education level extraction."""
    
    def test_bachelors_detection(self):
        """Test detection of bachelor's degree."""
        text = "Bachelor of Science in Computer Science"
        level = extract_education_level(text)
        self.assertEqual(level, "bachelors")
    
    def test_masters_detection(self):
        """Test detection of master's degree."""
        text = "Master's in Data Science"
        level = extract_education_level(text)
        self.assertEqual(level, "masters")


class SkillCategoryTests(TestCase):
    """Test skill categorization."""
    
    def test_programming_language_categorization(self):
        """Test categorization of programming languages."""
        skills = ["python", "java", "javascript"]
        categorized = categorize_skills(skills)
        self.assertIn("programming_languages", categorized)


class IntegrationTests(TestCase):
    """Integration tests for full matching algorithm."""
    
    def setUp(self):
        """Create test user and profile."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            name='Test Developer',
            email='test@example.com',
            phone='1234567890',
            skills='Python, Django, PostgreSQL, Docker, AWS',
            education='Bachelor of Science in Computer Science',
            expirence='8 years as a backend engineer',
            summery='Experienced backend engineer with strong Python skills',
            is_current=True
        )
    
    def test_excellent_match(self):
        """Test excellent match scenario."""
        job_description = """
        Senior Backend Engineer
        Requirements: 5+ years, Python, Django, PostgreSQL, Docker, AWS
        """
        
        score, reasons, missing, suggestions = calculate_match_score(
            self.profile, job_description
        )
        
        self.assertGreaterEqual(score, 50)
        self.assertGreater(len(reasons), 0)
