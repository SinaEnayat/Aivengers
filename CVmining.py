import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

import fitz  # PyMuPDF

# Local modules
from resume_mining.extractor import extract_text_from_pdf
from resume_mining.parser import parse_resume_text
from resume_mining.scorer_rule import score_resume_against_job
from resume_mining.scorer_ai import AIScorer
from resume_mining.enricher_ai import AIEnricher
from resume_mining.job_profile import create_job_profile_from_pdf
from resume_mining.github_validate import extract_github_user, fetch_public_repos, compute_validation_bonus


def _count_pdf_pages(pdf_path: Path) -> int:
    """Count the number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of pages in the PDF, or 0 if there's an error
    """
    try:
        with fitz.open(str(pdf_path)) as doc:
            return len(doc)
    except Exception:
        return 0


def _iter_pdfs(input_dir: Path, max_pages: int = None) -> List[Path]:
    """Get all PDF files in the input directory, optionally filtered by page count.

    Args:
        input_dir: Directory to search for PDFs
        max_pages: Maximum number of pages allowed (None for no limit)

    Returns:
        List of PDF file paths that meet the criteria
    """
    all_pdfs = [p for p in input_dir.glob("**/*.pdf") if p.is_file()]

    if max_pages is None:
        return all_pdfs

    filtered_pdfs = []
    for pdf_path in all_pdfs:
        page_count = _count_pdf_pages(pdf_path)
        if page_count > 0 and page_count <= max_pages:
            filtered_pdfs.append(pdf_path)
        elif page_count > max_pages:
            print(
                f"Skipping {pdf_path.name}: {page_count} pages (exceeds limit of {max_pages})")
        else:
            print(f"Skipping {pdf_path.name}: Could not read page count")

    return filtered_pdfs


def cmd_extract(args: argparse.Namespace) -> None:
    input_dir = Path(args.input_dir)
    output_jsonl = Path(args.output)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    pdf_paths = _iter_pdfs(input_dir, max_pages=args.max_pages)
    if not pdf_paths:
        print("No PDFs found that meet the criteria.")
        return

    results: List[Dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_pdf = {executor.submit(extract_text_from_pdf, str(
            pdf), args.ocr): pdf for pdf in pdf_paths}
        for future in as_completed(future_to_pdf):
            pdf_path = future_to_pdf[future]
            try:
                text = future.result()
            except Exception as exc:
                print(f"Error extracting {pdf_path}: {exc}")
                text = ""
            # Store only the filename to reduce prompt tokens
            parsed = parse_resume_text(
                text, source_file=os.path.basename(str(pdf_path)))
            results.append(parsed)

    with output_jsonl.open("w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Wrote {len(results)} records to {output_jsonl}")


def _load_jsonl(path: Path) -> List[Dict]:
    items: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _save_jsonl(items: List[Dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def cmd_score_rule(args: argparse.Namespace) -> None:
    resumes_path = Path(args.resumes)
    job_spec_path = Path(args.job_spec)
    output_path = Path(args.output)

    resumes = _load_jsonl(resumes_path)
    with job_spec_path.open("r", encoding="utf-8") as f:
        job_spec = json.load(f)

    scored = []
    for r in resumes:
        score_detail = score_resume_against_job(r, job_spec)
        row = {**r, **score_detail}
        scored.append(row)

    scored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    _save_jsonl(scored, output_path)
    print(
        f"Scored {len(scored)} resumes. Top score: {scored[0].get('score', 0.0) if scored else 0}")


def cmd_score_ai(args: argparse.Namespace) -> None:
    resumes_path = Path(args.resumes)
    job_spec_path = Path(args.job_spec)
    output_path = Path(args.output)

    resumes = _load_jsonl(resumes_path)
    with job_spec_path.open("r", encoding="utf-8") as f:
        job_spec = json.load(f)

    ai = AIScorer(
        provider=args.provider,
        model=args.model,
        api_base=os.getenv("AI_API_BASE"),
        api_key=os.getenv("AI_API_KEY"),
        batch_size=args.batch_size,
        max_retries=3,
    )
    if getattr(args, "stream", False):
        # truncate output and append incrementally per batch
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as _:
            pass
        total = len(resumes)
        done = 0
        for i in range(0, total, args.batch_size):
            batch = resumes[i: i + args.batch_size]
            try:
                batch_results = ai.score_resumes(batch, job_spec)
            except Exception as exc:
                print(
                    f"Scoring failed for batch {i // args.batch_size + 1}: {exc}")
                batch_results = []

            # GitHub validation bonus on batch
            github_token = os.getenv("GITHUB_TOKEN")
            for item in batch_results:
                links = item.get("links") or []
                username = extract_github_user(links)
                if not username:
                    continue
                try:
                    repos = fetch_public_repos(username, github_token)
                    criteria = job_spec.get("criteria") or []
                    bonus = compute_validation_bonus(repos, criteria)
                    item["score"] = round(
                        float(item.get("score", 0)) + bonus, 2)
                except Exception as exc:
                    print(f"GitHub validation failed for {username}: {exc}")

            # append results incrementally
            with output_path.open("a", encoding="utf-8") as f:
                for it in batch_results:
                    f.write(json.dumps(it, ensure_ascii=False) + "\n")
                    done += 1
            print(f"AI-scored {done}/{total} resumes -> {output_path}")
    else:
        results = ai.score_resumes(resumes, job_spec)

        # GitHub validation bonus
        github_token = os.getenv("GITHUB_TOKEN")
        for item in results:
            links = item.get("links") or []
            username = extract_github_user(links)
            if not username:
                continue
            try:
                repos = fetch_public_repos(username, github_token)
                criteria = job_spec.get("criteria") or []
                bonus = compute_validation_bonus(repos, criteria)
                item["score"] = round(float(item.get("score", 0)) + bonus, 2)
            except Exception as exc:
                print(f"GitHub validation failed for {username}: {exc}")

        results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        _save_jsonl(results, output_path)
        print(
            f"AI-scored {len(results)} resumes. Top score: {results[0].get('score', 0.0) if results else 0}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Persian resume mining and scoring")
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser(
        "extract", help="Extract and parse PDFs into JSONL")
    p_extract.add_argument("input_dir", help="Directory containing PDFs")
    p_extract.add_argument(
        "--output", default="out/resumes.jsonl", help="Output JSONL path")
    p_extract.add_argument("--workers", type=int,
                           default=4, help="Parallel workers")
    p_extract.add_argument("--ocr", action="store_true",
                           help="Enable OCR fallback for scanned PDFs")
    p_extract.add_argument("--max-pages", type=int, default=2,
                           help="Maximum number of pages allowed in PDFs (default: 2)")
    p_extract.set_defaults(func=cmd_extract)

    p_score = sub.add_parser(
        "score", help="Rule-based scoring against a job spec JSON")
    p_score.add_argument("resumes", help="Input JSONL from extract")
    p_score.add_argument("job_spec", help="Job spec JSON path")
    p_score.add_argument(
        "--output", default="out/scored_rule.jsonl", help="Output JSONL path")
    p_score.set_defaults(func=cmd_score_rule)

    p_ai = sub.add_parser("score-ai", help="AI-based scoring with batching")
    p_ai.add_argument("resumes", help="Input JSONL from extract")
    p_ai.add_argument("job_spec", help="Job spec JSON path")
    p_ai.add_argument("--output", default="out/scored_ai.jsonl",
                      help="Output JSONL path")
    p_ai.add_argument("--provider", default="openai",
                      choices=["openai", "azure"], help="AI provider")
    p_ai.add_argument("--model", default="GPT-5-c5zn8", help="Model name")
    p_ai.add_argument("--batch-size", type=int, default=25,
                      help="Number of resumes per request")
    p_ai.add_argument("--stream", action="store_true",
                      help="Process incrementally and append results per batch (use with --batch-size 1 for per-line)")
    p_ai.set_defaults(func=cmd_score_ai)

    # Create job profile from JD PDF (Gemini/OpenAI)
    def cmd_job_profile(args: argparse.Namespace) -> None:
        jd_pdf = Path(args.jd_pdf)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        if args.provider == "openai":
            api_key = os.getenv("AI_API_KEY")
            api_base = os.getenv("AI_API_BASE")
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            api_base = None
        profile = create_job_profile_from_pdf(
            str(jd_pdf), api_key=api_key, model=args.model, provider=args.provider, api_base=api_base)
        with output.open("w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        print(f"Wrote job profile to {output}")

    p_jp = sub.add_parser(
        "job-profile", help="Create job profile JSON from a Persian JD PDF using Gemini or OpenAI")
    p_jp.add_argument("jd_pdf", help="Job description PDF path")
    p_jp.add_argument("--provider", default="openai",
                      choices=["gemini", "openai"], help="LLM provider")
    p_jp.add_argument("--model", default="GPT-5-c5zn8",
                      help="Model name (GPT-5-c5zn8 or gemini-1.5-pro)")
    p_jp.add_argument("--output", default="out/job_profile.json",
                      help="Output profile path")
    p_jp.set_defaults(func=cmd_job_profile)

    # Enrich resumes JSONL via AI to standardize fields
    def cmd_enrich_ai(args: argparse.Namespace) -> None:
        input_path = Path(args.input)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        resumes = _load_jsonl(input_path)
        enricher = AIEnricher(
            provider=args.provider,
            model=args.model,
            api_base=os.getenv("AI_API_BASE"),
            api_key=os.getenv("AI_API_KEY"),
            batch_size=args.batch_size,
            max_retries=3,
        )

        if getattr(args, "stream", False):
            # Truncate output then append incrementally per batch
            with output_path.open("w", encoding="utf-8") as _:
                pass
            total = len(resumes)
            done = 0
            for i in range(0, total, args.batch_size):
                batch = resumes[i: i + args.batch_size]
                try:
                    enriched_batch = enricher.enrich(batch)
                except Exception as exc:
                    print(
                        f"Enrichment failed for batch {i // args.batch_size + 1}: {exc}")
                    enriched_batch = batch  # fall back to original
                with output_path.open("a", encoding="utf-8") as f:
                    for item in enriched_batch:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
                        done += 1
                print(f"AI-enriched {done}/{total} resumes -> {output_path}")
        else:
            enriched = enricher.enrich(resumes)
            _save_jsonl(enriched, output_path)
            print(f"AI-enriched {len(enriched)} resumes -> {output_path}")

    p_enrich = sub.add_parser(
        "enrich-ai", help="AI-enrich parsed resumes JSONL to normalized schema")
    p_enrich.add_argument("input", help="Input resumes JSONL (from extract)")
    p_enrich.add_argument(
        "--output", default="out/resumes_enriched.jsonl", help="Output JSONL path")
    p_enrich.add_argument("--provider", default="openai",
                          choices=["openai"], help="AI provider")
    p_enrich.add_argument("--model", default="GPT-5-c5zn8", help="Model name")
    p_enrich.add_argument("--batch-size", type=int,
                          default=20, help="Items per request")
    p_enrich.add_argument("--stream", action="store_true",
                          help="Process incrementally and append results per batch (use with --batch-size 1 for per-line)")
    p_enrich.set_defaults(func=cmd_enrich_ai)

    # Ranking to CSV
    def cmd_rank(args: argparse.Namespace) -> None:
        scored_path = Path(args.scored)
        out_path = Path(args.output)
        items = _load_jsonl(scored_path)
        items.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for it in items:
                name = it.get("source_file") or it.get("name") or "unknown"
                f.write(f"{name},{it.get('score', 0)}\n")
        print(f"Wrote ranking to {out_path}")

    p_rank = sub.add_parser(
        "rank", help="Produce ranked CSV from scored JSONL")
    p_rank.add_argument("scored", help="Scored JSONL path")
    p_rank.add_argument(
        "--output", default="out/results.csv", help="Output CSV")
    p_rank.set_defaults(func=cmd_rank)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
