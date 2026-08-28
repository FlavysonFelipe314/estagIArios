from flask import Blueprint, current_app, jsonify, request

from .schemas import ValidationError, parse_plan_request
from .services.plan_service import AIPlanError, create_plan

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return {"status": "ok", "service": "nutriplan-api"}


@api.post("/plans")
def generate_plan():
    try:
        data = parse_plan_request(request.get_json(silent=True))
    except ValidationError as error:
        return jsonify({"error": "Dados inválidos", "fields": error.fields}), 422
    try:
        plan = create_plan(
            data,
            current_app.config.get("PLAN_AGENT"),
            current_app.config.get("PLAN_FORMATTER"),
        )
    except AIPlanError as error:
        return jsonify({"error": "Falha na geração por IA", "message": str(error)}), 502
    return jsonify(plan), 201
