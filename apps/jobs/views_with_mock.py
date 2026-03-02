from django.shortcuts import render
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.users.models import Profile
from apps.match.matching import calculate_match_score, extract_skills_from_text
import os

# Use mock data for development if API quota exceeded
USE_MOCK_JOBS = os.getenv('USE_MOCK_JOBS', 'False') == 'True'

MOCK_JOBS = [
    {
        "job_id": "mock_1",
        "job_title": "Senior React Developer",
        "employer_name": "TechCorp Solutions",
        "job_location": "Remote",
        "job_employment_type": "FULLTIME",
        "job_description": "Looking for an experienced React developer with expertise in JavaScript, TypeScript, and modern web development. Must have experience with Redux, responsive design, and REST APIs.",
    },
    {
        "job_id": "mock_2",
        "job_title": "Frontend Engineer",
        "employer_name": "Digital Innovations Inc",
        "job_location": "San Francisco, CA",
        "job_employment_type": "FULLTIME",
        "job_description": "Seeking Frontend Engineer with strong JavaScript and HTML5/CSS3 skills. Experience with React, Bootstrap, and responsive design required. Knowledge of Git and npm required.",
    },
    {
        "job_id": "mock_3",
        "job_title": "Full Stack Developer",
        "employer_name": "Web Solutions Ltd",
        "job_location": "New York, NY",
        "job_employment_type": "FULLTIME",
        "job_description": "Full stack position requiring JavaScript, React, Node.js, and SQL knowledge. Must have experience with REST APIs, MongoDB, Firebase, and Git. Strong problem-solving and team collaboration skills.",
    },
    {
        "job_id": "mock_4",
        "job_title": "JavaScript Developer",
        "employer_name": "CloudTech Systems",
        "job_location": "Remote",
        "job_employment_type": "FULLTIME",
        "job_description": "Experienced JavaScript developer needed. Core requirements: TypeScript, ES6+, HTML5, CSS3, responsive design. Nice to have: React experience, REST API integration, npm ecosystem knowledge.",
    },
    {
        "job_id": "mock_5",
        "job_title": "UI/UX Developer",
        "employer_name": "Design Studios Pro",
        "job_location": "Austin, TX",
        "job_employment_type": "CONTRACT",
        "job_description": "Looking for talented UI/UX developer. Must have expertise in HTML5, CSS3, Bootstrap framework, responsive design. React and JavaScript proficiency required. Strong design thinking and creativity skills.",
    },
]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_matching_jobs(request):
    """
    Fetch jobs from JSearch API and calculate match scores using enhanced algorithm.
    Filters and sorts jobs by match quality.
    Supports fallback to mock data if API quota exceeded.
    """
    headers = {
        'x-rapidapi-key': "b31f7e6ccamshb505afe9264b9d4p11d38ejsn39a5aa53d1e9",
        'x-rapidapi-host': "jsearch.p.rapidapi.com"
    }
    
    try:
        profile = Profile.objects.get(user=request.user, is_current=True)
    except Profile.DoesNotExist:
        return Response({"error": "Current profile not found."}, status=404)
    
    # Get search keywords from user profile skills
    if profile.skills and profile.skills != "Not Provided" and profile.skills != "Skills not found":
        # Extract actual skills from the formatted profile skills text using the same algorithm
        # that normalizes skills for matching
        extracted_skills = extract_skills_from_text(profile.skills)
        
        if extracted_skills:
            # Use top 4-5 most relevant extracted skills for job search
            top_skills = list(extracted_skills)[:min(5, len(extracted_skills))]
            keywords = " ".join(top_skills)
        else:
            # Fallback: use first few words if extraction fails
            words = profile.skills.split()[:5]
            keywords = " ".join(words)
    else:
        return Response({"error": "No skills defined in profile."}, status=400)
    
    # Get filter parameters
    location = request.query_params.get("location", "")
    employment_type = request.query_params.get("employment_type", "")
    min_match_score = int(request.query_params.get("min_match_score", 40))
    pages = int(request.query_params.get("pages", 3))  # Number of pages to fetch
    
    all_jobs = []
    rate_limit_error = False
    
    # Try real API first, fallback to mock data if needed
    if not USE_MOCK_JOBS:
        params = {
            "query": keywords,
            "page": "1",
            "results_per_page": "10",
        }
        
        if location:
            params["location"] = location
        if employment_type:
            params["employment_type"] = employment_type
        
        # Fetch jobs from multiple pages
        for page_num in range(1, pages + 1):
            params["page"] = str(page_num)
            try:
                response = requests.get(
                    "https://jsearch.p.rapidapi.com/search",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    jobs = response.json().get("data", [])
                    all_jobs.extend(jobs)
                elif response.status_code == 429:
                    # Rate limit reached - use mock data fallback
                    rate_limit_error = True
                    all_jobs = MOCK_JOBS
                    break
                else:
                    # Check if it's a quota error message
                    try:
                        error_data = response.json()
                        if "quota" in str(error_data).lower() or "exceeded" in str(error_data).lower():
                            # Use mock data for quota exceeded
                            all_jobs = MOCK_JOBS
                            break
                    except:
                        pass
                    
                    return Response(
                        {"error": f"Failed to fetch jobs: {response.status_code}"},
                        status=500
                    )
            except requests.exceptions.RequestException as e:
                # If API request fails, fall back to mock data
                all_jobs = MOCK_JOBS
                break
    else:
        # Development mode: use mock jobs
        all_jobs = MOCK_JOBS
    
    if not all_jobs:
        return Response({
            "matches": [],
            "summary": {
                "total_jobs_found": 0,
                "filtered_matches": 0,
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0,
            }
        })
    
    # Calculate matches and filter
    matching_jobs = []
    
    for job in all_jobs:
        # Combine job details for better matching
        job_title = job.get('job_title', '')
        job_desc = job.get('job_description', '') or job.get('description', '')
        job_description = f"{job_title} {job_desc}"
        
        # Use enhanced matching algorithm
        score, reasons, missing_skills, suggestions = calculate_match_score(profile, job_description)
        
        # Filter by minimum match score
        if score >= min_match_score:
            job_data = job.copy()
            job_data["match_score"] = score
            job_data["match_reasons"] = reasons
            job_data["missing_skills"] = missing_skills
            job_data["match_suggestions"] = suggestions
            matching_jobs.append(job_data)
    
    # Sort by match score (highest first)
    matching_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Generate summary statistics
    summary = {
        "total_jobs_found": len(all_jobs),
        "filtered_matches": len(matching_jobs),
        "excellent": len([j for j in matching_jobs if j["match_score"] >= 75]),
        "good": len([j for j in matching_jobs if 60 <= j["match_score"] < 75]),
        "fair": len([j for j in matching_jobs if 40 <= j["match_score"] < 60]),
        "poor": len([j for j in matching_jobs if j["match_score"] < 40]),
    }
    
    return Response({
        "matches": matching_jobs[:20],  # Return top 20 matches
        "summary": summary,
        "profile_skills": profile.skills,
        "using_mock_data": rate_limit_error or USE_MOCK_JOBS
    })
