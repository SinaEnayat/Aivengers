from __future__ import annotations

from typing import Dict, List, Any

import re
from .normalize import normalize_persian


SECTION_PATTERNS = {
    "name": [r"(?:نام\s*[:：]\s*)(.+)", r"^([\u0600-\u06FF\s]+)$"],
    "title": [r"عنوان\s*شغلی\s*[:：]\s*(.+)", r"\b(مهندس|توسعه‌دهنده|مدیر|کارشناس)[\u0600-\u06FF\s]*"],
    "phone": [r"(?:(?:\+?98|0)9\d{9})"],
    "email": [r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"],
    "skills": [r"مهارت(?:‌|\s)*ها?\s*[:：]?\s*(.+)", r"Skills\s*[:：]?\s*(.+)"],
    "education": [r"تحصیلات|سوابق\s*تحصیلی|Education"],
    "experience": [r"سوابق\s*شغلی|تجربه(?:\s*کاری)?|Experience"],
}


def _extract_first(patterns: List[str], text: str, flags: int = re.MULTILINE) -> str:
    for pat in patterns:
        m = re.search(pat, text, flags)
        if m:
            return m.group(1) if m.groups() else m.group(0)
    return ""


def parse_resume_text(text: str, source_file: str = "") -> Dict[str, Any]:
    norm = normalize_persian(text)

    name = _extract_first(SECTION_PATTERNS["name"], norm)
    title = _extract_first(SECTION_PATTERNS["title"], norm)
    phone = _extract_first(SECTION_PATTERNS["phone"], norm, flags=0)
    email = _extract_first(SECTION_PATTERNS["email"], norm, flags=0)

    # skills: split by separators
    skills_block = _extract_first(
        [SECTION_PATTERNS["skills"][0], SECTION_PATTERNS["skills"][1]], norm)
    skills = []
    if skills_block:
        for token in re.split(r"[,،\u200c\s]+", skills_block):
            tok = token.strip(" ،,؛؛|/")
            if tok:
                skills.append(tok)

    # naive section slicing for education/experience
    edu_flag = re.search(SECTION_PATTERNS["education"][0], norm)
    exp_flag = re.search(SECTION_PATTERNS["experience"][0], norm)

    education = ""
    experience = ""
    if edu_flag and exp_flag:
        start = edu_flag.start()
        end = exp_flag.start() if exp_flag.start() > start else None
        education = norm[start:end].strip()
        # rest for experience
        experience = norm[exp_flag.start():].strip()
    elif edu_flag:
        education = norm[edu_flag.start():].strip()
    elif exp_flag:
        experience = norm[exp_flag.start():].strip()

    # links (URLs) extraction
    links: List[str] = []
    for m in re.finditer(r"https?://[^\s)\]}]+", norm):
        url = m.group(0).rstrip('،.؛')
        links.append(url)

    return {
        "source_file": source_file,
        "name": name,
        "title": title,
        "phone": phone,
        "email": email,
        "skills": skills,
        "education": education,
        "experience": experience,
        "links": links,
        "raw": norm[:5000],
    }
