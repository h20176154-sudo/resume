import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import openai
import groq

# Configure Groq as primary AI service
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Fallback OpenAI configuration (only used if Groq fails)
openai.api_key = os.environ.get('OPENAI_API_KEY')
if not openai.api_key:
    openai.api_key = None

# Initialize Groq client
groq_client = None
def get_groq_client():
    global groq_client
    
    if groq_client is None and GROQ_API_KEY:
        try:
            groq_client = groq.Groq(api_key=GROQ_API_KEY)
            print("Groq client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Groq client: {e}")
            groq_client = False  # Mark as failed to avoid retrying
    elif not GROQ_API_KEY:
        print("GROQ_API_KEY not found in environment variables")
        groq_client = False
    
    return groq_client

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_questions(request):
    """
    Generate multiple technical interview questions and answers for a given job and language.
    """
    try:
        data = request.data
        job = data.get('job', '').strip()
        lang = data.get('lang', '').strip()
        num = int(data.get('num', 5))  # default to 5 questions

        if not job or not lang:
            return Response(
                {'error': 'Job title and programming language are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        prompt = f"""
Generate {num} professional, non-repetitive technical interview questions
for a {job} focusing on {lang}. Provide both the question and the answer
in JSON format as an array like:
[
  {{"question": "Your Question?", "answer": "Answer here"}},
  ...
]
"""

        # Try Groq first (primary AI service)
        groq_client_instance = get_groq_client()
        if groq_client_instance:
            try:
                response = groq_client_instance.chat.completions.create(
                 model="openai/gpt-oss-20b", # Using Llama model instead of GPT
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                output = response.choices[0].message.content
                print("Successfully generated questions using Groq")
            except Exception as groq_error:
                print(f"Groq error: {groq_error}")
                groq_client_instance = None  # fallback to OpenAI

        # Fallback to OpenAI only if Groq fails
        if not groq_client_instance:
            if not GROQ_API_KEY:
                return Response(
                    {'error': 'GROQ_API_KEY not configured. Please set GROQ_API_KEY environment variable.'}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            try:
                # Check if OpenAI API key is available for fallback
                if not openai.api_key or openai.api_key == "sk-proj-your-actual-openai-api-key-here":
                    return Response(
                        {'error': 'Both Groq and OpenAI API keys are not configured. Please set GROQ_API_KEY environment variable.'}, 
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                
                print("Falling back to OpenAI...")
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                output = response.choices[0].message.content
                print("Successfully generated questions using OpenAI fallback")
            except Exception as openai_error:
                print(f"OpenAI error: {openai_error}")
                return Response(
                    {'error': f'Both AI services unavailable. Groq error: {str(groq_error) if "groq_error" in locals() else "Unknown"}, OpenAI error: {str(openai_error)}'}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

        # Remove ```json formatting if present
        if output.startswith("```"):
            output = "\n".join(output.split("\n")[1:-1])

        try:
            questions_with_answers = json.loads(output)
            return Response({"questions_with_answers": questions_with_answers})
        except Exception as parse_error:
            return Response({
                "error": "Failed to parse AI output",
                "details": str(parse_error),
                "raw_output": output
            })

    except Exception as e:
        print(f"Unexpected error in generate_questions: {e}")
        return Response(
            {'error': 'An unexpected error occurred'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def ask_question(request):
    """
    Answer a manual interview question
    """
    try:
        data = request.data
        question = data.get('question', '').strip()
        
        if not question:
            return Response(
                {'error': 'Question is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Construct the prompt for answering
        prompt = f"""
You are an expert technical interviewer and mentor. Please provide a comprehensive answer to this interview question:

Question: {question}

Provide a detailed answer that includes:
1. Clear explanation of the concept
2. Key points and details
3. Examples or code snippets where relevant
4. Best practices
5. Common pitfalls or considerations
6. Real-world applications

Format your answer in a clear, structured way that would help someone prepare for a technical interview.
"""

        # Try Groq first (primary AI service)
        groq_client_instance = get_groq_client()
        if groq_client_instance:
            try:
                response = groq_client_instance.chat.completions.create(
                 model="openai/gpt-oss-20b", 
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                answer = response.choices[0].message.content
                print("Successfully answered question using Groq")
            except Exception as groq_error:
                print(f"Groq error: {groq_error}")
                groq_client_instance = None  # fallback to OpenAI
        
        # Fallback to OpenAI only if Groq fails
        if not groq_client_instance:
            if not GROQ_API_KEY:
                return Response(
                    {'error': 'GROQ_API_KEY not configured. Please set GROQ_API_KEY environment variable.'}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            try:
                # Check if OpenAI API key is available for fallback
                if not openai.api_key or openai.api_key == "sk-proj-your-actual-openai-api-key-here":
                    return Response(
                        {'error': 'Both Groq and OpenAI API keys are not configured. Please set GROQ_API_KEY environment variable.'}, 
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                
                print("Falling back to OpenAI...")
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                answer = response.choices[0].message.content
                print("Successfully answered question using OpenAI fallback")
            except Exception as openai_error:
                print(f"OpenAI error: {openai_error}")
                return Response(
                    {'error': f'Both AI services unavailable. Groq error: {str(groq_error) if "groq_error" in locals() else "Unknown"}, OpenAI error: {str(openai_error)}'}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        
        return Response({
            'answer': answer,
            'question': question
        })
        
    except Exception as e:
        print(f"Unexpected error in ask_question: {e}")
        return Response(
            {'error': 'An unexpected error occurred'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def test_endpoint(request):
    """
    Test endpoint to verify the service is working
    """
    return Response({
        'status': 'success',
        'message': 'Interview Practice API is working',
        'endpoints': {
            'generate_questions': 'POST /interview-practice/generate-questions/',
            'ask_question': 'POST /interview-practice/ask-question/',
            'test': 'GET /interview-practice/test/'
        }
    })