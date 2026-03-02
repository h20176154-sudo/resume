import json
import os
import re
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import QuizSession, QuizScore

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')


def get_groq_client():
    """Get Groq client instance."""
    if not GROQ_API_KEY or not GROQ_AVAILABLE:
        return None
    try:
        return groq.Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return None


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_quiz(request):
    """
    Generate MCQ questions using Groq API and store them.
    Expects: { "language": "Python", "count": 5 }
    """
    try:
        data = request.data
        language = data.get('language', 'Python').strip()
        count = int(data.get('count', 5))
        count = max(1, min(50, count))  # Clamp between 1-50

        groq_client = get_groq_client()
        if not groq_client:
            return Response(
                {'error': 'GROQ_API_KEY not configured. Set GROQ_API_KEY environment variable.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        prompt = f"""Generate {count} MCQ questions on {language}.

Rules:
- 4 options per question
- 1 correct answer per question
- JSON only, no explanation
- Use clear, distinct option labels (A, B, C, D or full option text)

Format:
[
  {{
    "question": "Your question here?",
    "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
    "answer": "Option A text"
  }}
]

Return only valid JSON array."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4000
        )

        content = response.choices[0].message.content
        content = re.sub(r'```json|```', '', content)
        content = content.strip()

        quiz = json.loads(content)
        if not isinstance(quiz, list):
            return Response({'error': 'Invalid JSON from AI'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Normalize questions: ensure options and answer exist
        normalized = []
        for q in quiz:
            if isinstance(q, dict) and q.get('question'):
                opts = q.get('options', [])
                ans = q.get('answer', '')
                if isinstance(opts, list) and opts and ans:
                    normalized.append({
                        'question': q['question'],
                        'options': [str(o) for o in opts],
                        'answer': str(ans)
                    })
        quiz = normalized[:count]

        # Store in database
        user = request.user if request.user.is_authenticated else None
        session = QuizSession.objects.create(
            user=user,
            language=language,
            question_count=len(quiz),
            questions=quiz
        )

        return Response({
            'quiz': quiz,
            'session_id': session.id
        })

    except json.JSONDecodeError as e:
        return Response({'error': f'Invalid JSON: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_quiz(request):
    """
    Submit quiz answers, calculate score, store it.
    Expects: { "session_id": 1, "answers": ["A", "B", "C", ...] }
    """
    try:
        data = request.data
        session_id = data.get('session_id')
        answers = data.get('answers', [])

        if not session_id:
            return Response({'error': 'session_id required'}, status=status.HTTP_400_BAD_REQUEST)

        session = QuizSession.objects.filter(id=session_id).first()
        if not session:
            return Response({'error': 'Quiz session not found'}, status=status.HTTP_404_NOT_FOUND)

        questions = session.questions
        total = len(questions)
        score = 0

        for i, q in enumerate(questions):
            if i < len(answers) and answers[i] == q.get('answer'):
                score += 1

        # Store score
        user = request.user if request.user.is_authenticated else None
        QuizScore.objects.create(
            user=user,
            quiz_session=session,
            score=score,
            total=total
        )

        return Response({
            'score': score,
            'total': total,
            'percentage': round(100 * score / total, 1) if total else 0
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def quiz_history(request):
    """Get user's quiz scores (if authenticated)."""
    if not request.user.is_authenticated:
        return Response({'scores': []})

    scores = QuizScore.objects.filter(user=request.user).select_related('quiz_session').order_by('-created_at')[:20]
    data = [
        {
            'id': s.id,
            'score': s.score,
            'total': s.total,
            'percentage': round(100 * s.score / s.total, 1) if s.total else 0,
            'language': s.quiz_session.language,
            'created_at': s.created_at.isoformat()
        }
        for s in scores
    ]
    return Response({'scores': data})
