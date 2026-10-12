# AI-Powered Career Coach Platform

A local web application that analyses a resume against a target job role and returns an ATS score, a skill-gap report, free course suggestions, and interview practice with graded feedback.

Everything runs on the user's own machine. No cloud API, no API key, no per-request cost.

## Features

- **Resume parsing** — extracts contact details, sections, skills and bullet statistics from PDF or DOCX
- **ATS scoring** — a score out of 100 across six checks, with a plain-English list of what to fix
- **Skill gap analysis** — weighted match percentage against the must-have and good-to-have skills of a target role
- **Course recommendation** — curated free course links for every missing skill
- **Interview preparation** — 8 generated questions per role, and a 0-10 grade with feedback on any answer typed in

Scoring adapts to the candidate. With 0 years of experience the Projects section is checked; with 1 year or more the Work Experience section is checked instead.

## Design decision: rules for numbers, LLM for language

Every number in this project is produced by deterministic Python code. The model is never asked to score anything.

Asking an LLM to "rate this resume out of 100" returns a different number on every run, because generation is sampled. A score that changes between runs cannot be trusted or defended.

| Job | Handled by |
| --- | --- |
| ATS score, section checks, bullet counts | `engine.py` (rules) |
| Skill detection and matching | `engine.py` (regex + dictionary) |
| Skill gap percentage | `engine.py` (weighted formula) |
| Interview questions | `llm.py` (Ollama) |
| Grading a typed answer | `llm.py` (Ollama) |

## Tech stack

| Layer | Choice |
| --- | --- |
| Backend | Flask 3.1.3 |
| Templates | Jinja2 via `DictLoader` |
| UI | Bootstrap 5.3 (CDN) |
| Database | SQLite |
| Auth | Flask-Login + bcrypt |
| PDF reading | pdfplumber |
| DOCX reading | python-docx |
| LLM runtime | Ollama + qwen2.5:3b |

## Why qwen2.5:3b

Developed on an 8 GB RAM laptop with integrated graphics, so the model runs on CPU.

| Option | Size | Runs on 8 GB? |
| --- | --- | --- |
| Llama 3.1 8B | 4.7 GB | No — system swaps |
| Qwen 2.5 7B | 4.7 GB | No |
| **Qwen 2.5 3B** | **1.9 GB** | **Yes — ~2.5 GB resident** |

Among the models that fit, Qwen 2.5 3B was chosen for structured output: every call in this project asks for JSON, and it follows a key schema more reliably than similarly sized alternatives.

Both the model name and endpoint live in `config.py`, so switching to a larger model or a hosted endpoint is a one-line change.

## ATS scoring rubric

| Check | Max | How it is scored |
| --- | --- | --- |
| Contact Details | 10 | Email 4, phone 3, LinkedIn or GitHub 3 |
| Resume Sections | 20 | 5 points per required section found |
| Role Keyword Match | 30 | 20 weighted to must-have skills, 10 to good-to-have |
| ATS Formatting | 20 | Bullets used 7, no tables 7, contact at top 6 |
| Quantified Impact | 10 | Scales with the share of bullets containing numbers |
| Resume Length | 10 | Full marks between 350 and 900 words |

## Setup

**1. Install Ollama** from [ollama.com/download](https://ollama.com/download) and pull the model:

```
ollama pull qwen2.5:3b
```

**2. Create the environment** (Python 3.12 or newer):

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Run:**

```
python app.py
```

Open `http://127.0.0.1:5000`. The database and uploads folder are created on first run.

Interview Prep needs Ollama running. Everything else works without it.

## Project structure

```
career_coach/
├── app.py            Flask routes, auth, database setup
├── engine.py         Parsing and all rule-based scoring
├── llm.py            Ollama calls
├── templates.py      Jinja templates in a TEMPLATES dict
├── config.py         Paths, limits, model name
├── data.json         Skills, roles, courses
└── requirements.txt
```

## Adding a target role

No code change needed. Add an entry to the `roles` object in `data.json`:

```json
"Your Role Name": {
  "must_have": ["skill1", "skill2"],
  "good_to_have": ["skill3", "skill4"]
}
```

It appears in the profile dropdown on the next page load.

## Limitations

- Keyword matching is literal — "GitHub" on a resume does not satisfy a "git" requirement
- Scanned (image-only) PDFs are rejected; no OCR
- Target roles come from a fixed list of 11
- Generation takes 30-60 seconds per call on CPU
- Development server only; not configured for deployment

## Planned next

- Paste a job description instead of selecting a role
- Download the analysis as a PDF report
- Progress chart of ATS score across re-uploads
- A bullet rewriter that returns a quantified version of a weak bullet