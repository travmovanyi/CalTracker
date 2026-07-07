"""
Розрахунок добової норми калорій за формулою Міффліна-Сан Жеора.
"""

ACTIVITY_LEVELS = {
    "Мінімальна (сидяча робота, без спорту)": 1.2,
    "Легка (1-3 тренування/тиждень)": 1.375,
    "Середня (3-5 тренувань/тиждень)": 1.55,
    "Висока (6-7 тренувань/тиждень)": 1.725,
    "Дуже висока (фізична праця + спорт)": 1.9,
}

MIN_SAFE_CALORIES_MALE = 1500
MIN_SAFE_CALORIES_FEMALE = 1200


def calculate_bmr(gender: str, weight: float, height: float, age: int) -> float:
    if gender == "male":
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161


def calculate_tdee(bmr: float, activity_factor: float) -> float:
    return bmr * activity_factor


def calculate_daily_goal(gender: str, weight: float, height: float, age: int,
                          target_weight: float, activity_factor: float) -> dict:
    """
    Повертає денну норму калорій з урахуванням цілі (схуднення/набір/підтримка).
    Дефіцит/надлишок — не більше ~20% від TDEE, з нижньою межею безпеки.
    """
    bmr = calculate_bmr(gender, weight, height, age)
    tdee = calculate_tdee(bmr, activity_factor)

    diff = target_weight - weight  # від'ємне = схуднення

    if diff < -0.5:
        goal_type = "схуднення"
        deficit = min(500, tdee * 0.2)
        daily_goal = tdee - deficit
    elif diff > 0.5:
        goal_type = "набір ваги"
        surplus = min(400, tdee * 0.15)
        daily_goal = tdee + surplus
    else:
        goal_type = "підтримка ваги"
        daily_goal = tdee

    min_safe = MIN_SAFE_CALORIES_MALE if gender == "male" else MIN_SAFE_CALORIES_FEMALE
    if daily_goal < min_safe:
        daily_goal = min_safe

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "daily_goal": round(daily_goal),
        "goal_type": goal_type,
    }
