from pydantic import BaseModel, Field


class AIFoodItem(BaseModel):
    name: str = Field(min_length=2, description="Nome do alimento em português")
    amount: str = Field(min_length=2, description="Porção prática, como 120 g ou 1 unidade")
    kcal: int = Field(ge=0, le=2000)
    protein: int = Field(ge=0, le=300, description="Proteínas em gramas")
    carbs: int = Field(ge=0, le=500, description="Carboidratos em gramas")
    fat: int = Field(ge=0, le=250, description="Gorduras em gramas")


class AIMeal(BaseModel):
    name: str = Field(min_length=2, description="Ex.: Café da manhã, almoço ou lanche")
    time: str = Field(description="Horário sugerido no formato HH:MM")
    items: list[AIFoodItem] = Field(min_length=2, max_length=5)


class AISubstitution(BaseModel):
    food: str = Field(min_length=2, description="Alimento e porção que serão substituídos")
    options: list[str] = Field(min_length=1, max_length=3, description="Alternativas com porções equivalentes")


class AIPlan(BaseModel):
    target_kcal: int = Field(ge=1200, le=5000, description="Meta calórica diária aproximada")
    strategy: str = Field(min_length=20, max_length=500, description="Resumo da estratégia usada na personalização")
    meals: list[AIMeal] = Field(min_length=3, max_length=6)
    substitutions: list[AISubstitution] = Field(min_length=2, max_length=6)
    notice: str = Field(min_length=20, max_length=300, description="Aviso educativo, sem caráter de prescrição")
