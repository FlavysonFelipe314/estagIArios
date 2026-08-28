"""Ponto de entrada compatível com `python app.py` e `flask --app app run`."""

from nutrition_app import create_app
from nutrition_app.agent import create_nutrition_agent, create_nutrition_formatter

agent = create_nutrition_agent()
formatter = create_nutrition_formatter()
app = create_app({"PLAN_AGENT": agent, "PLAN_FORMATTER": formatter})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
