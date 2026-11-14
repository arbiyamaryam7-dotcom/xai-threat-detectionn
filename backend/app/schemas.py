"""Pydantic request/response models."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class FlowInput(BaseModel):
    features: dict[str, float] = Field(..., description="CIC-IDS2017 style flow features, name -> value")
    source_ip: str | None = Field(None, max_length=45)


class PredictionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    source_ip: str | None
    destination_port: int | None
    predicted_class: str
    confidence: float
    anomaly_score: float
    is_alert: bool
    true_label: str | None


class PredictionDetail(PredictionRow):
    features: dict
    explanation: dict | None
    missing_features: int = 0


class AlertUpdate(BaseModel):
    status: Literal["open", "acknowledged", "resolved", "false_positive"]
