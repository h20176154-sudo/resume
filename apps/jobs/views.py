import os
import re
from html import unescape

import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.match.matching import calculate_match_score, extract_skills_from_text
from apps.users.models import Profile


ACTIVE_JOBS_URL = "https://active-jobs-db.p.rapidapi.com/modified-ats-24h"
REMOTIVE_URL = "https://remotive.com/api/remote-jobs"


def _clean_text(value):
    if not value:
        return ""
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_job_item(job_id, title, company, location_text, employment, description, apply_url, logo=""):
    return {
        "job_id": str(job_id or ""),
        "job_title": title or "",
        "employer_name": company or "",
        "employer_logo": logo or "",
        "job_location": location_text or "",
        "job_employment_type": employment or "",
        "job_description": description or "",
        "job_apply_link": apply_url or "",
        "apply_url": apply_url or "",
        "apply_options": [{"publisher": company or "Apply", "apply_link": apply_url}] if apply_url else [],
    }


def _filter_with_keywords(text_blob, keyword_terms):
    if not keyword_terms:
        return True
    lowered = text_blob.lower()
    return any(term in lowered for term in keyword_terms)


def _job_key(job_item):
    return "::".join([
        str(job_item.get("job_id", "")),
        str(job_item.get("job_title", "")),
        str(job_item.get("employer_name", "")),
        str(job_item.get("job_apply_link", "")),
    ])


def _merge_unique_jobs(base_jobs, new_jobs, max_count):
    seen = {_job_key(j) for j in base_jobs}
    merged = list(base_jobs)
    for job in new_jobs:
        key = _job_key(job)
        if key in seen:
            continue
        merged.append(job)
        seen.add(key)
        if len(merged) >= max_count:
            break
    return merged


def _build_job_candidates(raw_jobs, location, employment_type, keyword_terms, active_schema=True, enforce_keywords=True, limit=None):
    filtered = []

    for job in raw_jobs:
        if active_schema:
            title = _clean_text(job.get("title") or job.get("job_title"))
            description = _clean_text(job.get("description") or job.get("job_description"))
            company = _clean_text(job.get("organization") or job.get("company_name") or job.get("company"))
            city = _clean_text(job.get("city"))
            country = _clean_text(job.get("country"))
            location_text = ", ".join([part for part in [city, country] if part])
            employment = _clean_text(job.get("employment_type") or job.get("job_type"))
            apply_url = (
                job.get("url")
                or job.get("linkedin_org_url")
                or job.get("linkedin_job_url_cleaned")
                or job.get("redirect_url")
                or ""
            )
            logo = ""
            job_id = job.get("id")
        else:
            title = _clean_text(job.get("title"))
            description = _clean_text(job.get("description"))
            company = _clean_text(job.get("company_name"))
            location_text = _clean_text(job.get("candidate_required_location"))
            employment = _clean_text(job.get("job_type"))
            apply_url = job.get("url") or ""
            logo = job.get("company_logo_url") or ""
            job_id = job.get("id")

        searchable = f"{title} {description} {company}"
        if enforce_keywords and not _filter_with_keywords(searchable, keyword_terms):
            continue
        if location and location.lower() not in location_text.lower():
            continue
        if employment_type and employment_type.lower() not in employment.lower():
            continue

        filtered.append(
            _normalize_job_item(
                job_id,
                title,
                company,
                location_text,
                employment,
                description,
                apply_url,
                logo=logo,
            )
        )

        if limit and len(filtered) >= limit:
            break

    return filtered


def _fetch_active_jobs(limit, location, employment_type, keyword_terms, rapidapi_key):
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "active-jobs-db.p.rapidapi.com",
    }
    params = {
        "limit": str(limit),
        "offset": "0",
        "description_type": "text",
    }

    response = requests.get(ACTIVE_JOBS_URL, headers=headers, params=params, timeout=30)

    if response.status_code != 200:
        return [], response.status_code

    raw_jobs = response.json()
    if not isinstance(raw_jobs, list):
        return [], 200

    filtered = _build_job_candidates(
        raw_jobs,
        location,
        employment_type,
        keyword_terms,
        active_schema=True,
        enforce_keywords=True,
    )

    if not filtered and keyword_terms:
        filtered = _build_job_candidates(
            raw_jobs,
            location,
            employment_type,
            keyword_terms,
            active_schema=True,
            enforce_keywords=False,
        )

    return filtered, 200


def _fetch_remotive_jobs(limit, location, employment_type, keyword_terms):
    # Intentionally do not send narrow search terms to avoid returning only 1 repeated job.
    response = requests.get(REMOTIVE_URL, timeout=30)
    if response.status_code != 200:
        return [], response.status_code

    raw_jobs = response.json().get("jobs", [])

    filtered = _build_job_candidates(
        raw_jobs,
        location,
        employment_type,
        keyword_terms,
        active_schema=False,
        enforce_keywords=True,
        limit=limit,
    )

    if not filtered and keyword_terms:
        filtered = _build_job_candidates(
            raw_jobs,
            location,
            employment_type,
            keyword_terms,
            active_schema=False,
            enforce_keywords=False,
            limit=limit,
        )

    return filtered[:limit], 200


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def fetch_matching_jobs(request):
    """
    Fetch jobs from Active Jobs DB API (primary) and calculate match scores.
    Falls back to Remotive when Active Jobs DB is unauthorized/rate-limited.
    """
    try:
        profile = Profile.objects.get(user=request.user, is_current=True)
    except Profile.DoesNotExist:
        return Response({"error": "Current profile not found."}, status=404)

    if profile.skills and profile.skills != "Not Provided" and profile.skills != "Skills not found":
        extracted_skills = extract_skills_from_text(profile.skills)
        if extracted_skills:
            top_skills = list(extracted_skills)[: min(3, len(extracted_skills))]
            keywords = " ".join(top_skills)
        else:
            keywords = " ".join(profile.skills.split()[:3])
    else:
        return Response({"error": "No skills defined in profile."}, status=400)

    location = request.query_params.get("location", "")
    employment_type = request.query_params.get("employment_type", "")

    try:
        min_match_score = int(request.query_params.get("min_match_score", 25))
    except (TypeError, ValueError):
        return Response({"error": "min_match_score must be an integer."}, status=400)

    try:
        pages = int(request.query_params.get("pages", 3))
    except (TypeError, ValueError):
        return Response({"error": "pages must be an integer."}, status=400)

    try:
        desired_results = int(request.query_params.get("results", 20))
    except (TypeError, ValueError):
        return Response({"error": "results must be an integer."}, status=400)

    desired_results = max(5, min(desired_results, 50))
    limit = max(desired_results * 5, 10, min(pages, 5) * 100)
    keyword_terms = [term.lower() for term in keywords.split() if term.strip()]
    rapidapi_key = os.getenv("RAPIDAPI_KEY", "a7e71d1b97msh7a530ec813d0990p100653jsn72111c93e56e")

    warnings = []
    source = "active_jobs_db"

    try:
        all_jobs, active_status = _fetch_active_jobs(
            limit=limit,
            location=location,
            employment_type=employment_type,
            keyword_terms=keyword_terms,
            rapidapi_key=rapidapi_key,
        )
    except requests.exceptions.Timeout:
        all_jobs, active_status = [], 503
    except requests.exceptions.RequestException:
        all_jobs, active_status = [], 503

    if active_status != 200:
        if active_status in (401, 403, 429):
            source = "remotive_fallback"
            warnings.append(
                "Primary provider returned "
                f"{active_status}. Using fallback jobs source. "
                "To use Active Jobs DB, verify RapidAPI subscription and key."
            )
            try:
                all_jobs, remotive_status = _fetch_remotive_jobs(
                    limit=limit,
                    location=location,
                    employment_type=employment_type,
                    keyword_terms=keyword_terms,
                )
            except requests.exceptions.Timeout:
                remotive_status = 503
                all_jobs = []
            except requests.exceptions.RequestException:
                remotive_status = 503
                all_jobs = []

            if remotive_status != 200:
                return Response(
                    {"error": f"Failed to fetch jobs from both providers ({active_status}, {remotive_status})."},
                    status=503,
                )
        else:
            return Response({"error": f"Failed to fetch jobs: {active_status}"}, status=503)

    # Top-up from fallback source if primary/fallback still returned too few jobs.
    if len(all_jobs) < desired_results:
        try:
            topup_jobs, topup_status = _fetch_remotive_jobs(
                limit=limit,
                location=location,
                employment_type=employment_type,
                keyword_terms=keyword_terms,
            )
        except requests.exceptions.RequestException:
            topup_jobs, topup_status = [], 503

        if topup_status == 200 and topup_jobs:
            before_count = len(all_jobs)
            all_jobs = _merge_unique_jobs(all_jobs, topup_jobs, limit)
            added = len(all_jobs) - before_count
            if added > 0:
                warnings.append(f"Added {added} extra jobs from fallback source to provide broader results.")

    if not all_jobs:
        payload = {
            "matches": [],
            "summary": {
                "total_jobs_found": 0,
                "filtered_matches": 0,
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0,
            },
            "source": source,
        }
        if warnings:
            payload["warning"] = " ".join(warnings)
        return Response(payload)

    scored_jobs = []
    matching_jobs = []

    for job in all_jobs:
        job_title = job.get("job_title", "")
        job_desc = job.get("job_description", "")
        job_description = f"{job_title} {job_desc}".strip()

        score, reasons, missing_skills, suggestions = calculate_match_score(profile, job_description)

        job_data = job.copy()
        job_data["match_score"] = score
        job_data["match_reasons"] = reasons
        job_data["missing_skills"] = missing_skills
        job_data["match_suggestions"] = suggestions
        if not job_data.get("apply_url"):
            job_data["apply_url"] = job_data.get("job_apply_link") or ""

        scored_jobs.append(job_data)
        if score >= min_match_score:
            matching_jobs.append(job_data)

    scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    matching_jobs.sort(key=lambda x: x["match_score"], reverse=True)

    strict_count = len(matching_jobs)
    target_count = min(desired_results, len(scored_jobs))

    if target_count > strict_count:
        existing_keys = {_job_key(j) for j in matching_jobs}
        for candidate in scored_jobs:
            key = _job_key(candidate)
            if key in existing_keys:
                continue
            matching_jobs.append(candidate)
            existing_keys.add(key)
            if len(matching_jobs) >= target_count:
                break

    matching_jobs = matching_jobs[:target_count] if target_count > 0 else []

    if scored_jobs and strict_count == 0:
        warnings.append(
            f"No jobs reached minimum match score {min_match_score}. Showing best available results instead."
        )
    elif scored_jobs and strict_count < target_count:
        warnings.append(
            f"Only {strict_count} jobs reached minimum match score {min_match_score}. Filled remaining with best available jobs."
        )

    summary = {
        "total_jobs_found": len(all_jobs),
        "filtered_matches": len(matching_jobs),
        "excellent": len([j for j in matching_jobs if j["match_score"] >= 75]),
        "good": len([j for j in matching_jobs if 60 <= j["match_score"] < 75]),
        "fair": len([j for j in matching_jobs if 40 <= j["match_score"] < 60]),
        "poor": len([j for j in matching_jobs if j["match_score"] < 40]),
    }

    payload = {
        "matches": matching_jobs[:desired_results],
        "summary": summary,
        "profile_skills": profile.skills,
        "source": source,
    }
    if warnings:
        payload["warning"] = " ".join(warnings)

    return Response(payload)
