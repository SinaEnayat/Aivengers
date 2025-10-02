from __future__ import annotations

from typing import Any, Dict, List

import json
import time


class AIScorer:
    def __init__(
            self,
            provider: str,
            model: str,
            api_base: str | None,
            api_key: str | None,
            batch_size: int = 25,
            max_retries: int = 3,
    ):
        self.provider = provider
        self.model = model
        self.api_base = api_base
        self.api_key = api_key
        self.batch_size = max(1, batch_size)
        self.max_retries = max(0, max_retries)

    def _build_prompt(self, job: Dict[str, Any], resumes: List[Dict[str, Any]]) -> str:
        return (
            "You are an HR assistant fluent in Persian. Score each resume 0-100 based on weighted criteria.\n"
            "Criteria is provided as job_profile.criteria with priority and weight.\n"
            "For each resume, provide structured reasoning with these exact sections:\n"
            "1. دلایل گرفتن امتیاز: (Reasons for getting points)\n"
            "2. دلایل نگرفتن امتیاز: (Reasons for not getting points)\n"
            "Return strict JSON list: [{source_file, score, reasoning}].\n"
            "The reasoning field should contain the structured analysis with the two sections above.\n"
            f"Job Spec: {json.dumps(job, ensure_ascii=False)}\n"
            f"Resumes: {json.dumps(resumes, ensure_ascii=False)}\n"
        )

    def _call_openai(self, prompt: str) -> str:
        # Lazy import to avoid hard dependency if unused
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return resp.choices[0].message.content or "[]"

    def _parse_scores(self, content: str) -> List[Dict[str, Any]]:
        # Try to find JSON block
        try:
            return json.loads(content)
        except Exception:
            # Best effort: find first JSON array
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(content[start: end + 1])
                except Exception:
                    pass
        return []

    def score_resumes(self, resumes: List[Dict[str, Any]], job: Dict[str, Any]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for i in range(0, len(resumes), self.batch_size):
            batch = resumes[i: i + self.batch_size]
            prompt = self._build_prompt(job, [{"source_file": r.get("source_file"), "title": r.get(
                "title"), "skills": r.get("skills"), "experience": r.get("experience")} for r in batch])
            attempt = 0
            while True:
                try:
                    if self.provider == "openai":
                        content = self._call_openai(prompt)
                    else:
                        raise NotImplementedError(
                            f"Provider {self.provider} not implemented")
                    scores = self._parse_scores(content)
                    # Merge back by source_file
                    index = {r.get("source_file"): r for r in batch}
                    for s in scores:
                        src = s.get("source_file")
                        if src in index:
                            merged = {
                                **index[src], "score": s.get("score", 0), "ai_reason": s.get("reasoning", "")}
                            results.append(merged)
                    break
                except Exception as exc:
                    attempt += 1
                    if attempt > self.max_retries:
                        raise
                    time.sleep(1.5 * attempt)
        return results
