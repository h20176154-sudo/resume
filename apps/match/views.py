from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.models import Profile
from apps.users.serializers import Profileserilizer
from . matching import calculate_match_score
from django.core.cache import cache
import hashlib

class MatchJobDescriptionView(APIView):
    """
    Enhanced job matching endpoint with improved scoring algorithm.
    Accepts job description and returns detailed match analysis.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        job_description = request.data.get("job_description", "")
        
        if not job_description.strip():
            return Response({"error": "Job description cannot be empty."}, status=400)
        
        try:
            profile = Profile.objects.get(user=request.user, is_current=True)
        except Profile.DoesNotExist:
            return Response({"error": "Current profile not found."}, status=404)
        
        try:
            # Calculate match with enhanced algorithm
            score, reasons, missing_skills, suggestions = calculate_match_score(profile, job_description)
            
            return Response({
                "match_percentage": score,
                "reasons": reasons,
                "profile": Profileserilizer(profile).data,
                "missing_skills": missing_skills,
                "suggestions": suggestions,
            })
        except Exception as e:
            import traceback
            print(f"Error in calculate_match_score: {str(e)}")
            traceback.print_exc()
            return Response({"error": f"Error matching job description: {str(e)}"}, status=500)


class BatchJobMatchingView(APIView):
    """
    Enhanced batch job matching endpoint for processing multiple jobs efficiently.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Expected request format:
        {
            "jobs": [
                {"id": "job1", "title": "...", "description": "..."},
                {"id": "job2", "title": "...", "description": "..."}
            ]
        }
        """
        jobs = request.data.get("jobs", [])
        
        if not jobs:
            return Response({"error": "Jobs list cannot be empty."}, status=400)
        
        try:
            profile = Profile.objects.get(user=request.user, is_current=True)
        except Profile.DoesNotExist:
            return Response({"error": "Current profile not found."}, status=404)
        
        matched_jobs = []
        
        for job in jobs:
            job_id = job.get("id")
            job_title = job.get("title", "")
            job_description = job.get("description", "")
            
            # Combine title and description for better matching
            combined_text = f"{job_title} {job_description}"
            
            # Calculate match
            score, reasons, missing_skills, suggestions = calculate_match_score(profile, combined_text)
            
            matched_jobs.append({
                "id": job_id,
                "title": job_title,
                "match_percentage": score,
                "reasons": reasons,
                "missing_skills": missing_skills,
                "suggestions": suggestions,
            })
        
        # Sort by match percentage (highest first)
        matched_jobs.sort(key=lambda x: x["match_percentage"], reverse=True)
        
        return Response({
            "profile": Profileserilizer(profile).data,
            "total_jobs": len(matched_jobs),
            "matches": matched_jobs,
            "summary": {
                "excellent": len([j for j in matched_jobs if j["match_percentage"] >= 75]),
                "good": len([j for j in matched_jobs if 60 <= j["match_percentage"] < 75]),
                "fair": len([j for j in matched_jobs if 40 <= j["match_percentage"] < 60]),
                "poor": len([j for j in matched_jobs if j["match_percentage"] < 40]),
            }
        })
