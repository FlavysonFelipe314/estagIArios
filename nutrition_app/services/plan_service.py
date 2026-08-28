from datetime import date
from hashlib import sha1
import json
import re

from pydantic import ValidationError as PydanticValidationError

from ..models import AIPlan
from ..schemas import PlanRequest


class AIPlanError(RuntimeError):
    """Erro explícito do provedor; nunca é substituído por um plano mockado."""


def _request_message(data: PlanRequest):
    payload = {
        "name": data.name,
        "age": data.age,
        "sex": data.sex,
        "weight_kg": data.weight,
        "height_cm": data.height,
        "activity_level": data.activity,
        "goal": data.goal,
        "meal_count": data.meal_count,
        "preferred_foods": data.preferred_foods,
        "restrictions": data.restrictions,
    }
    return (
        "Crie agora um plano alimentar diário totalmente personalizado para os "
        "dados abaixo. Gere exatamente " + str(data.meal_count) + " refeições.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def _totals(items):
    return {
        key: sum(getattr(item, key) for item in items)
        for key in ("kcal", "protein", "carbs", "fat")
    }


def _message_content(result):
    if not result.get("messages"):
        raise ValueError("Resposta vazia")
    content = result["messages"][-1].content
    if isinstance(content, list):
        content = "".join(block.get("text", "") for block in content if isinstance(block, dict))
    if not isinstance(content, str):
        raise ValueError("Conteúdo da resposta inválido")
    return content


def _json_content(content):
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)


def _parse_agent_response(result, formatter, meal_count):
    structured = result.get("structured_response")
    if structured is not None:
        return structured if isinstance(structured, AIPlan) else AIPlan.model_validate(structured)
    content = _message_content(result)
    try:
        return AIPlan.model_validate_json(_json_content(content))
    except PydanticValidationError:
        if formatter is None:
            raise
    conversion_prompt = f"""
Converta o plano alimentar abaixo para JSON válido que siga EXATAMENTE o JSON
Schema fornecido. Preserve todos os alimentos, porções e valores criados pelo
agente. O array meals deve conter exatamente {meal_count} refeições. Não inclua
markdown, comentários ou chaves fora do schema.

JSON SCHEMA:
{json.dumps(AIPlan.model_json_schema(), ensure_ascii=False)}

PLANO CRIADO PELO AGENTE:
{content}
""".strip()
    formatted = formatter.invoke(conversion_prompt)
    return AIPlan.model_validate_json(_json_content(formatted.content))


def create_plan(data: PlanRequest, agent, formatter=None):
    if agent is None:
        raise AIPlanError("O agente nutricional não foi configurado.")
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": _request_message(data)}]})
        ai_plan = _parse_agent_response(result, formatter, data.meal_count)
    except (PydanticValidationError, TypeError, ValueError, KeyError) as error:
        raise AIPlanError("A IA retornou um plano fora do formato esperado. Tente novamente.") from error
    except Exception as error:
        raise AIPlanError("Não foi possível gerar o plano com a IA neste momento.") from error

    if len(ai_plan.meals) != data.meal_count:
        raise AIPlanError(
            f"A IA retornou {len(ai_plan.meals)} refeições, mas foram solicitadas {data.meal_count}. Tente novamente."
        )

    meals = []
    for order, meal in enumerate(ai_plan.meals, start=1):
        meals.append({
            "order": order,
            "name": meal.name,
            "time": meal.time,
            "image_position": "left" if order % 2 else "right",
            "items": [item.model_dump() for item in meal.items],
            "totals": _totals(meal.items),
        })
    daily_totals = {
        key: sum(meal["totals"][key] for meal in meals)
        for key in ("kcal", "protein", "carbs", "fat")
    }
    plan_key = f"{data.name}-{date.today().isoformat()}-{data.goal}-{daily_totals['kcal']}"
    return {
        "id": sha1(plan_key.encode()).hexdigest()[:10],
        "created_at": date.today().isoformat(),
        "person": {"name": data.name, "weight": data.weight},
        "goal": data.goal,
        "meal_count": data.meal_count,
        "target_kcal": ai_plan.target_kcal,
        "strategy": ai_plan.strategy,
        "meals": meals,
        "totals": daily_totals,
        "substitutions": [item.model_dump() for item in ai_plan.substitutions],
        "preferences_used": data.preferred_foods,
        "restrictions_considered": data.restrictions,
        "notice": ai_plan.notice,
        "generated_by": "ai",
    }
