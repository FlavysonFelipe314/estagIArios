from dataclasses import dataclass


class ValidationError(Exception):
    def __init__(self, fields):
        super().__init__("Dados inválidos")
        self.fields = fields


@dataclass(frozen=True)
class PlanRequest:
    name: str
    age: int
    sex: str
    weight: float
    height: float
    activity: str
    goal: str
    meal_count: int
    preferred_foods: list[str]
    restrictions: list[str]


def _text_list(value):
    parts = value if isinstance(value, list) else str(value or "").replace(";", ",").split(",")
    return [str(item).strip() for item in parts if str(item).strip()]


def parse_plan_request(payload):
    if not isinstance(payload, dict):
        raise ValidationError({"body": "Envie um objeto JSON."})
    fields = {}
    name = str(payload.get("name", "")).strip()
    if len(name) < 2:
        fields["name"] = "Informe seu nome."

    def number(key, label, minimum, maximum):
        try:
            value = float(payload.get(key))
            if not minimum <= value <= maximum:
                raise ValueError
            return value
        except (TypeError, ValueError):
            fields[key] = f"{label} deve estar entre {minimum} e {maximum}."
            return minimum

    age = int(number("age", "Idade", 16, 100))
    weight = number("weight", "Peso", 35, 300)
    height = number("height", "Altura", 130, 230)
    sex = str(payload.get("sex", "")).lower()
    activity = str(payload.get("activity", "")).lower()
    goal = str(payload.get("goal", "")).lower()
    if sex not in {"female", "male", "other"}:
        fields["sex"] = "Selecione uma opção."
    if activity not in {"sedentary", "light", "moderate", "active"}:
        fields["activity"] = "Selecione seu nível de atividade."
    if goal not in {"lose", "maintain", "gain"}:
        fields["goal"] = "Selecione um objetivo."
    meal_count = int(number("meal_count", "Número de refeições", 3, 6))
    if fields:
        raise ValidationError(fields)
    return PlanRequest(name, age, sex, weight, height, activity, goal, meal_count,
                       _text_list(payload.get("preferred_foods")),
                       _text_list(payload.get("restrictions")))
