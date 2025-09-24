from __future__ import annotations

from typing import Dict, Any, List

import re
import httpx


def extract_github_user(links: List[str]) -> str | None:
    for link in links or []:
        m = re.search(r"github\.com/([A-Za-z0-9-_.]+)/?", link)
        if m:
            return m.group(1)
    return None


def fetch_public_repos(username: str, token: str | None = None) -> List[Dict[str, Any]]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/users/{username}/repos"
    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()


def compute_validation_bonus(repos: List[Dict[str, Any]], job_criteria: List[Dict[str, Any]]) -> float:
    # Look for repo languages/description matching skill features
    features = {c.get("feature", "").lower()
                for c in job_criteria if c.get("type") == "skill"}
    bonus = 0.0
    for repo in repos:
        desc = (repo.get("description") or "").lower()
        lang = (repo.get("language") or "").lower()
        name = (repo.get("name") or "").lower()
        text = f"{name} {desc} {lang}"
        if any(f for f in features if f and f in text):
            bonus += 2.0  # +2 points for each aligned repo, capped later
    return min(bonus, 10.0)
