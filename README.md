# Job Posting Analyzer

A local-first tool that turns Workday job postings into structured, classified data using a locally-hosted LLM. Paste one or more Workday URLs, and the app scrapes each posting, runs it through an LLM pipeline, and returns a labelled dataset you can filter, browse, and export.

Built around University of Ottawa CUPE / TA postings, but any Workday-hosted posting that exposes `application/ld+json` job metadata will work.

## Features

- **Bulk URL ingestion** — paste URLs in any format (newlines, commas, spaces, prose); the app extracts them with a regex.
- **Structured scraping** — reads Workday's embedded JSON-LD to pull title, employer, location, posted/deadline dates, job ID, employment type, and description.
- **LLM classification** — each posting is scored against four fields:
  - `health_science_related` — matched against a reference list of HSS course codes/titles.
  - `masters_required` — `Yes` only when a master's is the minimum requirement.
  - `doctorate_required` — `Yes` only when a doctorate is the minimum requirement.
  - `language_of_work` — `English`, `French`, or `Bilingual`.
- **Live UI** — per-URL progress bar with elapsed-time counter, running on a worker thread so the UI stays responsive.
- **Results views** — metric tiles, filterable card view, sortable table view.
- **Export** — one-click CSV or JSON download of the full analyzed dataset.

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend | [Streamlit](https://streamlit.io/) (custom dark theme via CSS) |
| LLM pipeline | [Haystack](https://haystack.deepset.ai/) (`PromptBuilder` + `OllamaChatGenerator`) |
| Local inference | [Ollama](https://ollama.com/) running `ministral-3:8b` at `http://localhost:11434` |
| Scraping | `requests` + `BeautifulSoup` (parses JSON-LD) |
| Data | `pandas` |
| Concurrency | `threading` (per-URL workers for live progress) |

## Project Structure

```
job_analyzer/
├── frontend/
│   └── app.py                    # Streamlit UI, styling, session state, progress loop
├── scripts/
│   └── analyze.py                # Scraping + Haystack pipeline (build_pipeline, process_jobs)
├── prompts/
│   ├── templates/
│   │   └── job_analysis.py       # Classification prompt (instructions repeated pre/post for recall)
│   └── references/
│       └── health_science_courses.py  # Reference corpus of HSS course codes/titles
└── README.md
```

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running locally
- The classification model pulled:
  ```bash
  ollama pull ministral-3:8b
  ```

## Installation

```bash
pip install streamlit pandas requests beautifulsoup4 haystack-ai ollama-haystack tqdm
```

## Running

From the project root:

```bash
streamlit run frontend/app.py
```

Then:

1. Click **Load Pipeline** to initialize the Haystack + Ollama pipeline.
2. Paste one or more Workday URLs into the input area.
3. Click **Analyze**.
4. Browse results in the Cards / Table tabs, or export via the Export tab.

You can also run the analyzer headless:

```bash
python -m scripts.analyze
```

This runs the example URLs in `scripts/analyze.py` and prints the JSON result to stdout.

## Configuration

`build_pipeline()` in `scripts/analyze.py` accepts:

- `model` (default `"ministral-3:8b"`) — any Ollama-compatible model tag.
- `ollama_url` (default `"http://localhost:11434"`).
- `ollama_temperature` (default `0.0`) — kept at 0 for deterministic classification.
- `prompt_template` — override to change classification logic.

The generator uses `response_format="json"` so the model output is parsed directly with `json.loads`.

## How the Classification Works

The prompt in `prompts/templates/job_analysis.py` gives the model strict rules:
- Health-science relevance is decided **only** from the `Course Title:` / `Course Code:` fields in the posting, matched against the reference course list — faculty names are explicitly ignored.
- Master's / doctorate flags are set only when the degree is the stated *minimum* requirement.
- Language defaults to English if the `Language of Work:` field is empty, and is set to `Bilingual` when both languages are listed.

The instructions are repeated before and after the job text in the prompt to reinforce recall on small local models.

## Notes

- The live typing counter in the URL input is driven by a small data-URL iframe that forces Streamlit's `text_area` to commit on each typing pause. If a browser blocks cross-origin DOM access, it falls back to Streamlit's default blur-commit behaviour.
- Scraping depends on Workday emitting `<script type="application/ld+json">` with a complete `JobPosting` object — non-Workday or heavily customized postings may need a different extractor.
