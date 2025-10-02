# AIvengers Desktop Application

## How to Run

1. **Make sure you have PDF files** in a folder (the application filters for 1-2 page PDFs only)

2. **Run the application:**
   ```bash
   python gui_app.py
   ```

## Usage Instructions

### Step 1: Extract
- Click "Choose resumes folder" and select a folder containing PDF resumes
- Click "Start Extracting" to process the PDFs
- The app will show "No PDFs found" if the folder doesn't contain 1-2 page PDFs

### Step 2: Job Description  
- Click "Choose job description PDF" and select a job description PDF
- Click "Start Job Descriptioning" to create a job profile

### Step 3: Enrich
- Click "Start Enriching" to enhance the extracted resumes
- Shows progress like "1/32 enriched"

### Step 4: Score
- Click "Start Scoring" to score resumes against job requirements
- Shows progress like "1/32 scored"

### Step 5: Rank
- Click "Start Ranking" to generate final rankings
- Results will be displayed in the results area with scores and AI reasons

## Visual States

- **Green**: Ready to run
- **Yellow**: Processing or Warning
- **Red**: Completed successfully
- **Hover**: Lighter green when mouse hovers over cards

## Troubleshooting

- **"No PDFs found"**: Make sure your folder contains PDF files with 1-2 pages
- **Command failed**: Check that all dependencies are installed (`pip install -r requirements.txt`)
- **Import errors**: Make sure you're running from the project directory

## Commands Executed

The GUI runs these commands behind the scenes:

1. **Extract**: `python CVmining.py extract "folder_path" --max-pages 2 --ocr --workers 4 --output "out/resumes.jsonl"`
2. **Job Profile**: `python CVmining.py job-profile "pdf_path" --provider openai --model "gpt-5" --output "out/job_profile.json"`
3. **Enrich**: `python CVmining.py enrich-ai "out/resumes.jsonl" --stream --batch-size 1 --output "out/resumes_enriched.jsonl"`
4. **Score**: `python CVmining.py score-ai "out/resumes.jsonl" "samples/job_spec.json" --stream --batch-size 1 --output "out/scored_ai.jsonl"`
5. **Rank**: `python CVmining.py rank "out/scored_ai.jsonl" --output "out/final_results.csv"`


