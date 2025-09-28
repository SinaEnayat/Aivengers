from __future__ import annotations

from typing import Any, Dict, List

import json
import time


class AIEnricher:
    def __init__(
            self,
            provider: str,
            model: str,
            api_base: str | None,
            api_key: str | None,
            batch_size: int = 20,
            max_retries: int = 3,
    ):
        self.provider = provider
        self.model = model
        self.api_base = api_base
        self.api_key = api_key
        self.batch_size = max(1, batch_size)
        self.max_retries = max(0, max_retries)

    def _build_prompt(self, resumes: List[Dict[str, Any]]) -> str:
        schema_example = {
            "source_file": "E:/resumes/john.pdf",
            "name": "نام کامل",
            "title": "عنوان شغلی",
            "phone": "09xxxxxxxxx",
            "email": "example@mail.com",
            "skills": ["Python", "Django"],
            "education": "متن خلاصه تحصیلات",
            "experience": "متن خلاصه سابقه کاری",
            "links": ["https://github.com/user"],
            "raw": "-",
        }
        return (
            "شما یک دستیار HR مسلط به فارسی هستید. وظیفه شما پاکسازی/استانداردسازی فیلدهاست.\n"
            "برای هر رزومه ورودی، دقیقا همان اسکیمای JSON زیر را برگردانید، بدون فیلد اضافه یا کم: \n"
            f"Schema: {json.dumps(schema_example, ensure_ascii=False)}\n"
            "قوانین: \n"
            "- اگر مقدار فعلی قابل قبول است همان را حفظ کنید.\n"
            "- مهارت‌ها را به لیست استانداردی از توکن‌ها تبدیل کنید (بدون تکرار).\n"
            "- عنوان شغلی را به یک عبارت کوتاه و متداول تبدیل کنید.\n"
            "- خروجی فقط JSON آرایه باشد، بدون متن اضافی.\n"
            f"Resumes: {json.dumps(resumes, ensure_ascii=False)}\n"
        )

    def _call_openai(self, prompt: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            content = resp.choices[0].message.content or "[]"
            print(f"DEBUG: Model response length: {len(content)}")
            print(f"DEBUG: Model response preview: {content[:300]}...")
            return content
        except Exception as e:
            print(f"DEBUG: OpenAI API Error: {e}")
            print(f"DEBUG: Error type: {type(e)}")
            # Try to get more details about the error
            if hasattr(e, 'response'):
                print(
                    f"DEBUG: Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'Unknown'}")
                print(
                    f"DEBUG: Response text: {e.response.text if hasattr(e.response, 'text') else 'Unknown'}")
            raise

    def _parse_list(self, content: str) -> List[Dict[str, Any]]:
        print(f"DEBUG: AI Response length: {len(content)}")
        print(f"DEBUG: First 200 chars: {content[:200]}")
        print(f"DEBUG: Last 200 chars: {content[-200:]}")

        try:
            return json.loads(content)
        except Exception as e:
            print(f"DEBUG: JSON parse error: {e}")
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    json_content = content[start: end + 1]
                    print(f"DEBUG: Extracted JSON length: {len(json_content)}")
                    return json.loads(json_content)
                except Exception as e2:
                    print(f"DEBUG: Extracted JSON also failed: {e2}")
                    print(f"DEBUG: Extracted content: {json_content[:500]}")
            return []

    def enrich(self, resumes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for i in range(0, len(resumes), self.batch_size):
            batch = resumes[i: i + self.batch_size]
            minimal = [
                {
                    "source_file": r.get("source_file"),
                    "name": r.get("name"),
                    "title": r.get("title"),
                    "phone": r.get("phone"),
                    "email": r.get("email"),
                    "skills": r.get("skills"),
                    "education": r.get("education"),
                    "experience": r.get("experience"),
                    "links": r.get("links"),
                    "raw": r.get("raw"),
                }
                for r in batch
            ]
            prompt = self._build_prompt(minimal)
            attempt = 0
            while True:
                try:
                    if self.provider == "openai":
                        content = self._call_openai(prompt)
                    else:
                        raise NotImplementedError(
                            f"Provider {self.provider} not implemented")
                    enriched = self._parse_list(content)
                    # Merge by source_file to preserve any untouched fields
                    index = {r.get("source_file"): r for r in batch}
                    for item in enriched:
                        src = item.get("source_file")
                        if src in index:
                            merged = {**index[src], **item}
                            results.append(merged)
                    break
                except Exception:
                    attempt += 1
                    if attempt > self.max_retries:
                        raise
                    time.sleep(1.5 * attempt)
        return results
