# grounding_layer.py

from datetime import datetime

def get_temporal_state() -> dict:
    """
    Return a simulated environmental grounding context for temporal awareness.
    """
    now = datetime.now()

    # Core temporal data
    dt_str = now.strftime("%Y-%m-%d %H:%M")
    weekday = now.strftime("%A")
    hour = now.hour

    # Day state
    if 5 <= hour < 12:
        time_of_day = "morning"
        user_energy = "likely ramping up"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
        user_energy = "peak energy or focus zone"
    elif 17 <= hour < 21:
        time_of_day = "evening"
        user_energy = "beginning to wind down"
    else:
        time_of_day = "night"
        user_energy = "likely winding down or resting"

    # Season estimate (Northern Hemisphere logic)
    month = now.month
    if month in [12, 1, 2]:
        season = "winter"
    elif month in [3, 4, 5]:
        season = "spring"
    elif month in [6, 7, 8]:
        season = "summer"
    else:
        season = "autumn"

    is_weekend = weekday in ["Saturday", "Sunday"]

    return {
        "datetime": dt_str,
        "day_of_week": weekday,
        "is_weekend": is_weekend,
        "hour": hour,
        "time_of_day": time_of_day,
        "season": season,
        "user_energy_state": user_energy
    }
