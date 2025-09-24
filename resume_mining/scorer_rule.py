from __future__ import annotations

from typing import Dict, Any, List

import math


def _jaccard(a: List[str], b: List[str]) -> float:
    set_a = {x.strip().lower() for x in a if x}
    set_b = {x.strip().lower() for x in b if x}
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def score_resume_against_job(resume: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Simple rule score.

    job fields supported:
    - title_keywords: List[str]
    - required_skills: List[str]
    - nice_to_have_skills: List[str]
    - min_years_experience: int
    """
    resume_title = (resume.get("title") or "").lower()
    resume_skills = resume.get("skills") or []
    resume_experience_text = (resume.get("experience") or "")

    # Title score
    title_keywords = [t.lower() for t in job.get("title_keywords", [])]
    title_hits = sum(1 for t in title_keywords if t in resume_title)
    title_score = min(1.0, title_hits /
                      max(1, len(title_keywords))) if title_keywords else 0.0

    # Skills score
    required = job.get("required_skills", [])
    nice = job.get("nice_to_have_skills", [])
    req_score = _jaccard(resume_skills, required)
    nice_score = _jaccard(resume_skills, nice)

    # Experience: crude estimation by counting years patterns
    import re
    years = 0
    for m in re.finditer(r"(\d{1,2})\s*(?:سال|years?)", resume_experience_text):
        try:
            years = max(years, int(m.group(1)))
        except Exception:
            pass
    min_years = int(job.get("min_years_experience", 0))
    exp_score = 1.0 if years >= min_years and min_years > 0 else (
        years / min_years if min_years > 0 else 0.0)
    exp_score = max(0.0, min(1.0, exp_score))

    # Weighted sum
    weights = job.get(
        "weights", {"title": 0.2, "required": 0.5, "nice": 0.2, "experience": 0.1})
    score = (
        weights.get("title", 0.2) * title_score
        + weights.get("required", 0.5) * req_score
        + weights.get("nice", 0.2) * nice_score
        + weights.get("experience", 0.1) * exp_score
    )

    return {
        "score": round(float(score) * 100.0, 2),
        "title_score": round(title_score, 3),
        "required_skills_score": round(req_score, 3),
        "nice_skills_score": round(nice_score, 3),
        "experience_score": round(exp_score, 3),
    }
