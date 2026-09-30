import requests
import subprocess
from monitor.settings_manager import load_settings
from monitor.ui_worker import LATEST_STATE
from monitor.ai_context import build_context_prompt
from monitor.memory_engine import add_memory
from monitor.user_profile_engine import update_profile_from_chat
from monitor.secrets import HF_TOKEN

HF_API_URL = "https://router.huggingface.co/novita/v3/openai/chat/completions"


def smart_fallback(prompt, state):
    prompt_lower = prompt.lower().strip()
    fatigue = state.get("fatigue", 0)
    try:
        fatigue_val = float(fatigue)
    except Exception:
        fatigue_val = 0.0

    current_app = state.get("app", "your current task")
    category = state.get("category", "General")

    from storage.db import fatigue_to_focus_score, get_today_deep_work_stats, get_streak_count
    focus_score = fatigue_to_focus_score(fatigue_val)
    streak = get_streak_count()

    if "summar" in prompt_lower or "day" in prompt_lower or "how am i" in prompt_lower:
        stats = get_today_deep_work_stats()
        deep_h = stats.get("deep_work_sec", 0) / 3600.0
        distract_cnt = stats.get("distraction_count", 0)
        return (
            f"📊 Daily Summary:\n"
            f"• Deep Work: {deep_h:.1f} hours logged\n"
            f"• Current Focus Index: {focus_score}%\n"
            f"• Distraction Events: {distract_cnt}\n"
            f"• Active Streak: {streak} days\n\n"
            f"You are currently in {current_app} ({category}). "
            f"{'You are maintaining an excellent flow state!' if focus_score > 75 else 'Consider pacing your cognitive load to avoid end-of-day burnout.'}"
        )

    if "break" in prompt_lower or "tired" in prompt_lower or "rest" in prompt_lower:
        if focus_score < 60:
            return (
                "☕ Micro-Break Protocol (Recommended):\n"
                "1. Step away from all monitors for 5–10 minutes.\n"
                "2. 20-20-20 Rule: Look at an object 20 feet away for 20 seconds to ease ciliary eye muscle strain.\n"
                "3. Hydrate with 250ml of cold water to boost alertness."
            )
        return (
            "🌿 Quick Refresh Protocol:\n"
            "Try 2 minutes of Physiological Sigh breathing (two inhales through the nose, followed by one long exhale through the mouth). "
            "This rapidly resets autonomic nervous system tension."
        )

    if "losing focus" in prompt_lower or "distract" in prompt_lower or "focus" in prompt_lower:
        return (
            f"🧠 Focus Diagnostics:\n"
            f"Your current estimated focus is {focus_score}%. When attention begins to wander, it usually means:\n"
            f"1. Task ambiguity — define the very next micro-action in {current_app}.\n"
            f"2. Context switching residue — close unused browser tabs.\n"
            f"3. Cognitive depletion — switch to Focus Mode for a structured 25-minute sprint."
        )

    return (
        f"💡 Coach Insight: You are working on {current_app} with an estimated focus level of {focus_score}%. "
        f"To maximize deep work, eliminate secondary notification sounds and commit to a single deliverable for the next 30 minutes."
    )


def ask_ai(prompt: str):
    # print(f"[AI] ask_ai called with prompt: {prompt[:50]}...")
    settings = load_settings()

    if not settings.get("ai_enabled", False):
        return "AI is disabled. Enable it in Features."

    update_profile_from_chat(prompt)

    # 🧠 Build context-aware prompt
    context_prompt = build_context_prompt(prompt, LATEST_STATE)

    # 1️⃣ TRY OLLAMA (LOCAL AI)
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3", context_prompt],
            capture_output=True,
            text=True,
            timeout=8
        )

        if result.stdout and result.returncode == 0:
            response_text = result.stdout.strip()
            add_memory(prompt, response_text)
            return response_text

    except Exception:
        pass  # fallback to HF

    # 2️⃣ HUGGING FACE API (CLOUD AI)
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "messages": [{"role": "user", "content": context_prompt}],
            "max_tokens": 200,
            "temperature": 0.7
        }

        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                response_text = choices[0]["message"]["content"]
                add_memory(prompt, response_text)
                return response_text
            return smart_fallback(prompt, LATEST_STATE)

        return smart_fallback(prompt, LATEST_STATE)

    except Exception:
        return smart_fallback(prompt, LATEST_STATE)


def check_ai_status():
    try:
        subprocess.run(["ollama", "--version"], capture_output=True)
        return "Local AI (Ollama) available"
    except:
        return "Using Cloud AI (Hugging Face)"
