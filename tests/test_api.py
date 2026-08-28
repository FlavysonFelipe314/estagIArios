import unittest

from nutrition_app import create_app
from nutrition_app.models import AIFoodItem, AIMeal, AIPlan, AISubstitution

VALID_PAYLOAD = {
    "name": "João", "age": 29, "sex": "male", "weight": 78, "height": 178,
    "activity": "moderate", "goal": "gain", "meal_count": 4,
    "preferred_foods": "arroz, frango, banana", "restrictions": "lactose",
}


class FakeAgent:
    """Substitui apenas o provedor externo nos testes; a aplicação não possui fallback."""
    def __init__(self):
        self.last_input = None

    def invoke(self, agent_input):
        self.last_input = agent_input
        food = AIFoodItem(name="Arroz com frango", amount="200 g", kcal=350, protein=30, carbs=40, fat=8)
        meals = [AIMeal(name=f"Refeição {index}", time=f"{7 + index * 3:02d}:00", items=[food, food]) for index in range(4)]
        return {"structured_response": AIPlan(
            target_kcal=2800,
            strategy="Distribuição equilibrada de energia e proteína ao longo do dia.",
            meals=meals,
            substitutions=[
                AISubstitution(food="Arroz 100 g", options=["Batata 180 g"]),
                AISubstitution(food="Frango 150 g", options=["Patinho 130 g"]),
            ],
            notice="Estimativa educativa que não substitui avaliação de um nutricionista.",
        )}


class BrokenAgent:
    def invoke(self, _agent_input):
        raise RuntimeError("provider offline")


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.agent = FakeAgent()
        self.client = create_app({"TESTING": True, "PLAN_AGENT": self.agent}).test_client()

    def test_health(self):
        self.assertEqual(self.client.get("/api/health").status_code, 200)

    def test_create_plan_uses_agent_and_returns_exact_meal_count(self):
        response = self.client.post("/api/plans", json=VALID_PAYLOAD)
        plan = response.get_json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(plan["meals"]), 4)
        self.assertEqual(plan["generated_by"], "ai")
        prompt = self.agent.last_input["messages"][0]["content"]
        self.assertIn('"restrictions": [', prompt)
        self.assertIn('"lactose"', prompt)

    def test_invalid_request_has_field_errors(self):
        response = self.client.post("/api/plans", json={"name": ""})
        self.assertEqual(response.status_code, 422)
        self.assertIn("name", response.get_json()["fields"])

    def test_provider_failure_has_no_mock_fallback(self):
        client = create_app({"TESTING": True, "PLAN_AGENT": BrokenAgent()}).test_client()
        response = client.post("/api/plans", json=VALID_PAYLOAD)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.get_json()["error"], "Falha na geração por IA")


if __name__ == "__main__":
    unittest.main()
