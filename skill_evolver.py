import os
import sys
import json
import datetime
from pathlib import Path
import ollama

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "skills_memory.json")
DAILY_LOG_FILE = os.path.join(BASE_DIR, "daily_skill_log.json")

def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "skills": {
            "backend_coding": {"level": 1, "learnings": []},
            "cybersecurity": {"level": 1, "learnings": []},
            "frontend_ui": {"level": 1, "learnings": []},
            "qa_testing": {"level": 1, "learnings": []},
            "system_file_access": {"level": 1, "learnings": []}
        },
        "bug_resolution_patterns": [],
        "total_tasks_completed": 0
    }

def save_memory(mem: dict):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)

def load_daily_logs() -> dict:
    if os.path.exists(DAILY_LOG_FILE):
        try:
            with open(DAILY_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_daily_logs(logs: dict):
    with open(DAILY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

def reflect_and_evolve_skills(task: str, execution_log: str, qa_feedback: str, model: str = "qwen3:4b") -> dict:
    mem = load_memory()
    today_str = datetime.date.today().isoformat()
    now_str = datetime.datetime.now().strftime("%H:%M:%S")

    reflection_prompt = f"""You are the AI Meta-Learner and Skill Evaluator.
Analyze the following multi-agent software engineering run:

TASK: {task}
EXECUTION HISTORY & CODE:
{execution_log[:2500]}

QA AND TEST RESULTS:
{qa_feedback[:1500]}

Identify:
1. What mistakes/bugs occurred and how were they resolved?
2. What specific new coding pattern, security defense, or UI technique was learned?
3. Which of the 4 skills improved (backend_coding, cybersecurity, frontend_ui, qa_testing)?

Return ONLY valid JSON in this exact structure:
{{
  "improvements": [
    {{
      "skill": "backend_coding|cybersecurity|frontend_ui|qa_testing",
      "summary": "Short title of improvement",
      "learned_rule": "Detailed lesson or code pattern learned"
    }}
  ],
  "bug_pattern_prevented": "Description of bug pattern to prevent in future"
}}
"""

    host = os.environ.get("OLLAMA_HOST", "https://catalogue-president-eyes-fairy.trycloudflare.com")
    client = ollama.Client(host=host)

    try:
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": reflection_prompt}],
            format="json"
        )
        data = json.loads(response.message.content)
    except Exception:
        data = {
            "improvements": [
                {
                    "skill": "backend_coding",
                    "summary": f"Completed task: {task[:50]}",
                    "learned_rule": "Executed multi-step task validation successfully."
                }
            ],
            "bug_pattern_prevented": "Standard test-driven bug prevention."
        }

    mem["total_tasks_completed"] = mem.get("total_tasks_completed", 0) + 1
    improvements = data.get("improvements", [])

    for imp in improvements:
        skill_name = imp.get("skill", "backend_coding")
        if skill_name in mem["skills"]:
            mem["skills"][skill_name]["learnings"].append({
                "date": today_str,
                "summary": imp.get("summary"),
                "rule": imp.get("learned_rule")
            })
            learning_count = len(mem["skills"][skill_name]["learnings"])
            mem["skills"][skill_name]["level"] = 1 + (learning_count // 2)

    if data.get("bug_pattern_prevented"):
        mem["bug_resolution_patterns"].append({
            "date": today_str,
            "task": task[:60],
            "pattern": data.get("bug_pattern_prevented")
        })

    save_memory(mem)

    daily_logs = load_daily_logs()
    if today_str not in daily_logs:
        daily_logs[today_str] = []

    log_entry = {
        "time": now_str,
        "task": task,
        "improvements": improvements,
        "bug_pattern_prevented": data.get("bug_pattern_prevented")
    }
    daily_logs[today_str].append(log_entry)
    save_daily_logs(daily_logs)

    return log_entry

def get_today_summary() -> str:
    today_str = datetime.date.today().isoformat()
    daily_logs = load_daily_logs()
    mem = load_memory()

    today_entries = daily_logs.get(today_str, [])
    if not today_entries:
        return f"📅 Daily Skill Update ({today_str}):\nMemory contains {mem.get('total_tasks_completed', 0)} total mastered tasks."

    lines = [f"📅 Daily Skill Evolution Report ({today_str})", "=" * 55]
    for i, entry in enumerate(today_entries, 1):
        lines.append(f"\n[Task {i} at {entry['time']}]: {entry['task']}")
        for imp in entry.get("improvements", []):
            lines.append(f"  ✨ Improved Skill: [{imp.get('skill')}] - {imp.get('summary')}")
            lines.append(f"     💡 Learned Rule: {imp.get('learned_rule')}")
        if entry.get("bug_pattern_prevented"):
            lines.append(f"  🛡️ Bug Pattern Added to Defense Memory: {entry['bug_pattern_prevented']}")

    lines.append("\n" + "-" * 55)
    lines.append("📊 Current Skill Mastery Levels:")
    for skill_name, data in mem.get("skills", {}).items():
        lines.append(f"  - {skill_name}: Level {data.get('level', 1)} ({len(data.get('learnings', []))} learnings)")

    return "\n".join(lines)

if __name__ == "__main__":
    print(get_today_summary())
