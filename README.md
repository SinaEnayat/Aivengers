## Persian Resume Mining and Scoring

### Features
- Extract Persian text from PDFs with OCR fallback (Tesseract)
- Normalize Persian text (Hazm)
- Parse fields: name, title, phone, email, skills, education, experience
- Rule-based scoring vs job spec
- AI scoring with batching (OpenAI) to avoid giant single prompts
- Job profile creator from Persian JD PDF using Gemini or OpenAI
- GitHub validation bonus using public repos
- Ranking to CSV

### Install
1) Python 3.10+
2) Windows OCR deps:
   - Install Tesseract: `https://github.com/UB-Mannheim/tesseract/wiki`
   - Install Poppler: `https://github.com/oschwartz10612/poppler-windows`
   - Add both to PATH
3) Python libs:
```bash
pip install -r requirements.txt
```

### Usage
Create job profile from a Persian JD PDF (Gemini):
```bash
$env:GEMINI_API_KEY="your_key"
python CVmining.py job-profile E:\jd.pdf --output out/job_profile.json
```

Create job profile from a Persian JD PDF (OpenAI):
```bash
$env:AI_API_KEY="sk-..."  # optional: $env:AI_API_BASE for custom endpoints
python CVmining.py job-profile E:\jd.pdf --provider openai --model gpt-4o-mini --output out/job_profile.json
```

Extract resumes from PDFs:
```bash
python CVmining.py extract E:\resumes --output out/resumes.jsonl --ocr --workers 6
```

Rule-based scoring:
```bash
python CVmining.py score out/resumes.jsonl job_spec.json --output out/scored_rule.jsonl
```

AI scoring (batched) with GitHub validation bonus:
```bash
$env:AI_API_KEY="sk-..."
$env:GITHUB_TOKEN="ghp_..."  # optional
python CVmining.py score-ai out/resumes.jsonl job_spec.json --output out/scored_ai.jsonl --provider openai --model gpt-4o-mini --batch-size 25
```

Produce ranked CSV:
```bash
python CVmining.py rank out/scored_ai.jsonl --output out/results.csv
```

AI-enrich parsed resumes to normalized schema (OpenAI):
```bash
$env:AI_API_KEY="sk-..."  # optional: $env:AI_API_BASE
python CVmining.py enrich-ai out/resumes.jsonl --provider openai --model gpt-4o-mini --output out/resumes_enriched.jsonl --batch-size 20
```

### Job Spec JSON example
```json
{
  "title_keywords": ["توسعه دهنده", "مهندس نرم افزار"],
  "required_skills": ["Python", "Django", "PostgreSQL"],
  "nice_to_have_skills": ["Docker", "Kubernetes"],
  "min_years_experience": 3,
  "weights": {"title": 0.2, "required": 0.5, "nice": 0.2, "experience": 0.1}
}
```

### Notes on Persian OCR and parsing
- OCR is used only when no text layer is found. This saves cost and time.
- We batch AI requests (e.g., 25 resumes at a time) instead of one huge 1000-resume prompt.
- You can tune regexes in `resume_mining/parser.py` to better match your CV formats.

