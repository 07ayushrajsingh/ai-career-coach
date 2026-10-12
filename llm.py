import json
import re

import requests

import config


def ask(prompt, temperature=0.4, timeout=240):
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature}
    }

    try:
        res = requests.post(config.OLLAMA_URL, json=payload, timeout=timeout)
        res.raise_for_status()
        return res.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama is not running. Start it and try again.")
    except requests.exceptions.Timeout:
        raise RuntimeError("Model took too long to respond. Try again.")


def extract_json(text):
    # model often wraps output in code fences or adds a line before it
    text = re.sub(r"^```[a-z]*", "", text.strip())
    text = re.sub(r"```$", "", text.strip())

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        start = text.find("{")
        end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def generate_questions(target_role, experience_years, skills):
    level = "fresher" if float(experience_years or 0) < 1 else "%s years experienced" % experience_years
    skill_text = ", ".join(skills[:20]) if skills else "basic programming"

    prompt = """You are an interview panel member hiring for the role of %s.
The candidate is a %s and knows: %s

Generate exactly 8 interview questions for this candidate.
Mix them: 4 technical, 2 based on the listed skills, 2 behavioural.
Keep each question under 30 words.

Reply with ONLY a JSON array, no explanation before or after.
Each item must have exactly these keys: "type", "question", "hint".
"type" must be one of: Technical, Skill, Behavioural.
"hint" is one short line on what the interviewer wants to hear.""" % (
        target_role, level, skill_text)

    raw = ask(prompt, temperature=0.6)
    data = extract_json(raw)

    if not isinstance(data, list):
        return []

    questions = []
    for item in data:
        if isinstance(item, dict) and item.get("question"):
            questions.append({
                "type": str(item.get("type", "Technical"))[:20],
                "question": str(item["question"]),
                "hint": str(item.get("hint", "")),
            })

    return questions[:8]


def evaluate_answer(question, answer, target_role):
    prompt = """You are interviewing a candidate for the role of %s.

Question: %s
Candidate answer: %s

Rate this answer and reply with ONLY a JSON object, no text before or after.
Keys: "score" (number 0 to 10), "good" (what was right, one line),
"missing" (what was left out, one line), "better_answer" (an improved answer in 3 to 4 sentences).""" % (
        target_role, question, answer)

    raw = ask(prompt, temperature=0.3)
    data = extract_json(raw)

    if not isinstance(data, dict):
        return None

    try:
        score = int(float(data.get("score", 0)))
    except (TypeError, ValueError):
        score = 0

    return {
        "score": max(0, min(score, 10)),
        "good": str(data.get("good", "")),
        "missing": str(data.get("missing", "")),
        "better_answer": str(data.get("better_answer", "")),
    }


def resume_feedback(ats_result, gap, target_role):
    notes = " ".join(ats_result["notes"]) if ats_result["notes"] else "No major issue found."
    missing = ", ".join(gap["must_missing"] + gap["good_missing"]) or "none"

    prompt = """A candidate is targeting the role of %s.
Their resume scored %d out of 100 on an ATS check.
Issues found: %s
Skills missing for this role: %s

Write 4 short action points telling the candidate what to change in their resume.
Be specific and practical. Reply with ONLY a JSON array of 4 strings, nothing else.""" % (
        target_role, ats_result["total"], notes, missing)

    raw = ask(prompt, temperature=0.4)
    data = extract_json(raw)

    if not isinstance(data, list):
        return []

    return [str(x) for x in data if str(x).strip()][:4]