from monitor.user_profile_engine import load_profile, save_profile

TECH_KEYWORDS = ["python", "java", "api", "ml", "data", "code"]


def update_profile_from_chat(prompt: str):
    profile = load_profile()
    text = prompt.lower()

    if any(w in text for w in ["what is", "explain", "basic"]):
        profile["experience_level"] = "beginner"
    elif any(w in text for w in ["optimize", "architecture", "design pattern"]):
        profile["experience_level"] = "advanced"

    if "example" in text or "simple" in text:
        profile["learning_style"] = "simple"
    elif "detailed" in text or "in depth" in text:
        profile["learning_style"] = "detailed"

    for kw in TECH_KEYWORDS:
        if kw in text:
            profile["topics"][kw] = profile["topics"].get(kw, 0) + 1

    save_profile(profile)


def update_profile_from_behavior(patterns: dict):
    profile = load_profile()

    productivity = patterns.get("productivity_ratio", 0.5)
    distraction = patterns.get("distraction_ratio", 0.0)

    profile["focus_level"] = productivity
    profile["distraction_level"] = distraction

    if productivity < 0.4:
        profile["preferred_length"] = "short"
    elif productivity > 0.7:
        profile["preferred_length"] = "long"

    save_profile(profile)
