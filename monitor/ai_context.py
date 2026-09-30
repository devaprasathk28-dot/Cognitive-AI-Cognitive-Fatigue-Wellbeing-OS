from monitor.memory_engine import get_recent_context
from monitor.user_profile_engine import load_profile

def build_memory_context():

    history = get_recent_context()

    if not history:
        return ""

    context = "Recent conversation:\n"

    for item in history:
        context += f"User: {item['user']}\n"
        context += f"AI: {item['ai']}\n"

    return context


def build_profile_context():
    profile = load_profile()
    peak_hr = profile.get('peak_productivity_hour', 'Unknown')
    if isinstance(peak_hr, int):
        peak_hr = f"{peak_hr}:00"
    
    return f"""
User Profile:
- Experience: {profile.get('experience_level', 'beginner')}
- Focus Level: {profile.get('focus_level', 0.5)}
- Peak Productivity Hour: {peak_hr}
- Distraction Ratio: {profile.get('distraction_ratio', 0.0)*100:.0f}%
- Avg Session Length: {profile.get('avg_session_length', 0)/60:.1f} mins
"""


def build_context_prompt(user_prompt, state):

    memory_context = build_memory_context()
    profile_context = build_profile_context()

    fatigue = state.get("fatigue", 0)
    burnout = state.get("burnout", 0)
    category = state.get("category", "Unknown")
    app = state.get("app", "Unknown")
    hour = state.get("hour", 12)

    instructions = []

    if fatigue > 0.70:
        instructions.append("User is tired. Keep responses short and suggest a break.")

    if burnout > 0.60:
        instructions.append("User is stressed. Be supportive.")

    system_prompt = f"""
You are a smart Productivity AI companion.
Your goal is to help the user stay focused, manage their cognitive load, and prevent burnout.

User's current state:
- Fatigue Level: {fatigue * 100:.0f}% (0% is fresh, 100% is exhausted)
- Burnout Risk: {burnout * 100:.0f}%
- Current App: {app}
- Current Activity Category: {category}
- Current Time (Hour): {hour}

{profile_context}
{memory_context}

Provide personalized suggestions based on their state. 
For example, if fatigue is high (> 80%) and they are using Chrome (Browsing), say: "You seem fatigued after long browsing sessions. Consider a break."
If they are doing deep work and fatigue is low, encourage them. Be concise, professional, and friendly.

Instructions:
{" ".join(instructions)}
"""

    return system_prompt + "\nUser: " + user_prompt

