"""
IBM Watsonx.ai integration using IBM Granite models.
Includes AGENT_INSTRUCTIONS for full coach customization.
"""
import os
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# ─────────────────────────────────────────────
# AGENT INSTRUCTIONS  (edit to customise)
# ─────────────────────────────────────────────
AGENT_INSTRUCTIONS = {
    # Coach personality: motivational | strict | friendly | scientific
    "coach_personality": os.getenv("COACH_PERSONALITY", "motivational"),
    # Workout difficulty: beginner | intermediate | advanced
    "workout_difficulty": os.getenv("WORKOUT_DIFFICULTY", "intermediate"),
    # Prefer Indian food options in meal plans
    "indian_diet_preference": os.getenv("INDIAN_DIET_PREFERENCE", "true").lower() == "true",
    # Always append injury/medical disclaimers
    "safety_rules": os.getenv("SAFETY_RULES", "true").lower() == "true",
    # Motivation style: positive | tough-love | balanced
    "motivation_style": os.getenv("MOTIVATION_STYLE", "balanced"),
}

_PERSONALITY_PROMPTS = {
    "motivational": "You are an enthusiastic, energetic fitness coach who constantly encourages the user.",
    "strict": "You are a disciplined, no-nonsense personal trainer who pushes users to their limits.",
    "friendly": "You are a warm, supportive friend who happens to be a certified fitness expert.",
    "scientific": "You are a sports scientist who backs every recommendation with evidence-based research.",
}

_MOTIVATION_PROMPTS = {
    "positive": "Always use uplifting, positive language and celebrate every small win.",
    "tough-love": "Be direct and candid; hold users accountable while still being supportive.",
    "balanced": "Balance encouragement with honest, realistic feedback.",
}


def _build_system_prompt(user_profile=None):
    personality = AGENT_INSTRUCTIONS["coach_personality"]
    motivation = AGENT_INSTRUCTIONS["motivation_style"]
    difficulty = AGENT_INSTRUCTIONS["workout_difficulty"]
    indian_diet = AGENT_INSTRUCTIONS["indian_diet_preference"]
    safety = AGENT_INSTRUCTIONS["safety_rules"]

    persona = _PERSONALITY_PROMPTS.get(personality, _PERSONALITY_PROMPTS["motivational"])
    motiv = _MOTIVATION_PROMPTS.get(motivation, _MOTIVATION_PROMPTS["balanced"])

    system = (
        f"{persona} {motiv}\n\n"
        f"Default workout difficulty level: {difficulty}.\n"
    )

    if indian_diet:
        system += (
            "When suggesting meal plans, prefer Indian cuisine options such as dal, roti, rice, "
            "sabzi, idli, dosa, poha, upma, paneer dishes, lentils, and regional snacks. "
            "Always provide vegetarian alternatives.\n"
        )

    if safety:
        system += (
            "SAFETY RULE: Always remind users to consult a doctor before starting any new "
            "exercise or diet program, especially if they have existing health conditions. "
            "Never provide medical diagnoses or prescribe treatments.\n"
        )

    system += (
        "You are the AI fitness coach inside the Fitness Buddy app. "
        "You help users with personalised workout plans, home exercises, nutrition advice, "
        "BMI interpretation, daily habits, and motivation. "
        "Keep responses concise, actionable, and formatted with bullet points or numbered lists "
        "where appropriate. Use metric units (kg, cm, km) unless the user asks otherwise.\n"
    )

    if user_profile:
        system += f"\nUser Profile:\n{user_profile}\n"

    return system.strip()


def _get_model():
    api_key = os.getenv("WATSONX_API_KEY")
    project_id = os.getenv("WATSONX_PROJECT_ID")
    url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    model_id = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-3-8b-instruct")

    if not api_key or not project_id:
        raise EnvironmentError(
            "WATSONX_API_KEY and WATSONX_PROJECT_ID must be set in the .env file."
        )

    # IBM Cloud API keys must be the raw UUID — strip the "ApiKey-" prefix if present
    if api_key.startswith("ApiKey-"):
        api_key = api_key[len("ApiKey-"):]

    credentials = Credentials(url=url, api_key=api_key)
    client = APIClient(credentials)

    params = {
        GenParams.MAX_NEW_TOKENS: 1024,
        GenParams.TEMPERATURE: 0.7,
        GenParams.TOP_P: 0.9,
        GenParams.REPETITION_PENALTY: 1.1,
    }

    model = ModelInference(
        model_id=model_id,
        api_client=client,
        project_id=project_id,
        params=params,
    )
    return model


def chat_with_granite(user_message: str, history: list, user_profile: str = "") -> str:
    """
    Send a message to IBM Granite via Watsonx.ai and return the response.

    Args:
        user_message: Current user input.
        history: List of dicts with 'role' and 'content' keys (last N turns).
        user_profile: Optional user profile string for context.

    Returns:
        AI response string.
    """
    try:
        model = _get_model()
        system_prompt = _build_system_prompt(user_profile or None)

        # Build conversation string for Llama 3 instruct format
        conversation = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}<|eot_id|>"
        for turn in history[-10:]:   # Keep last 10 turns to stay within token limits
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role == "user":
                conversation += f"<|start_header_id|>user<|end_header_id|>\n{content}<|eot_id|>"
            else:
                conversation += f"<|start_header_id|>assistant<|end_header_id|>\n{content}<|eot_id|>"

        conversation += f"<|start_header_id|>user<|end_header_id|>\n{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"

        response = model.generate_text(prompt=conversation)
        return response.strip() if response else "I'm here to help! Please try again."

    except EnvironmentError as e:
        return f"⚠️ Configuration error: {e}"
    except Exception as e:
        return f"⚠️ AI service unavailable. Please check your IBM Watsonx credentials. Details: {str(e)}"


def generate_meal_plan(profile) -> dict:
    """Generate a one-day AI meal plan for the user profile."""
    indian = AGENT_INSTRUCTIONS["indian_diet_preference"]
    diet_note = "Prefer Indian cuisine. Include regional options." if indian else "Use a globally balanced diet."

    prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{_build_system_prompt()}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\nGenerate a one-day meal plan for:\n"
        f"- Goal: {profile.goal}\n"
        f"- TDEE: {profile.tdee} kcal/day\n"
        f"- Activity Level: {profile.activity_level}\n"
        f"- {diet_note}\n\n"
        "Format the response EXACTLY as:\n"
        "BREAKFAST: <items>\n"
        "LUNCH: <items>\n"
        "DINNER: <items>\n"
        "SNACKS: <items>\n"
        "TOTAL_CALORIES: <number>\n"
        "WATER_ML: <number>\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    )

    try:
        model = _get_model()
        response = model.generate_text(prompt=prompt)
        return _parse_meal_plan(response)
    except Exception as e:
        return {"error": str(e)}


def _parse_meal_plan(text: str) -> dict:
    result = {}
    for key, field in [
        ("BREAKFAST", "breakfast"), ("LUNCH", "lunch"),
        ("DINNER", "dinner"), ("SNACKS", "snacks"),
        ("TOTAL_CALORIES", "total_calories"), ("WATER_ML", "water_target_ml"),
    ]:
        for line in text.splitlines():
            if line.strip().upper().startswith(key + ":"):
                value = line.split(":", 1)[1].strip()
                if field in ("total_calories", "water_target_ml"):
                    try:
                        result[field] = int("".join(filter(str.isdigit, value)))
                    except ValueError:
                        result[field] = 0
                else:
                    result[field] = value
                break
    return result


def generate_workout_plan(profile) -> str:
    """Generate a personalised workout plan."""
    difficulty = AGENT_INSTRUCTIONS["workout_difficulty"]
    prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{_build_system_prompt()}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\nCreate a detailed weekly workout plan for:\n"
        f"- Goal: {profile.goal}\n"
        f"- Age: {profile.age}, Gender: {profile.gender}\n"
        f"- BMI: {profile.bmi} ({profile.bmi_category})\n"
        f"- Activity Level: {profile.activity_level}\n"
        f"- Difficulty: {difficulty}\n"
        "Include: exercises, sets, reps, rest periods, and home-friendly alternatives.\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    )
    try:
        model = _get_model()
        return model.generate_text(prompt=prompt)
    except Exception as e:
        return f"Could not generate workout plan: {e}"
