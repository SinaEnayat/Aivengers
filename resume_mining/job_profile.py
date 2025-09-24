from __future__ import annotations

from typing import Any, Dict

import json
from pathlib import Path

import fitz  # PyMuPDF


PROMPT_FA = (
    """
شما یک کارشناس ارشد جذب هستید. متن شرح شغل فارسی زیر را بخوانید و یک پروفایل شغلی ساختارمند JSON تولید کنید. باید معیارها (criteria) را با این فیلدها استخراج کنید:
- feature: نام مهارت/معیار (مثلاً «برنامه نویسی پایتون» یا «تجربه کاری»)
- type: یکی از [skill, experience_years, education, responsibility]
- value: فقط برای experience_years در صورت ذکر عدد
- priority: یکی از [mandatory, preferred]
- weight: عدد اعشاری 1 تا 10 بر حسب اهمیت متن
فقط JSON بازگردان. هیچ متن دیگری ننویس.
"""
).strip()


def _read_pdf_text(path: str) -> str:
    with fitz.open(path) as doc:
        return "\n".join(page.get_text("text") or "" for page in doc)


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model = model

    def generate_job_profile(self, jd_text: str) -> Dict[str, Any]:
        # minimal HTTP client without SDK
        import httpx
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": PROMPT_FA},
                        {"text": jd_text},
                    ]
                }
            ]
        }
        url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent"
        r = httpx.post(url, headers=headers, params=params,
                       json=body, timeout=60)
        r.raise_for_status()
        data = r.json()
        # Parse text
        text = data.get("candidates", [{}])[0].get(
            "content", {}).get("parts", [{}])[0].get("text", "{}")
        try:
            return json.loads(text)
        except Exception:
            # try to find json braces
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start: end + 1])
            raise


def create_job_profile_from_pdf(pdf_path: str, api_key: str | None, model: str = "gemini-1.5-pro") -> Dict[str, Any]:
    jd_text = _read_pdf_text(pdf_path)
    client = GeminiClient(api_key=api_key, model=model)
    return client.generate_job_profile(jd_text)
