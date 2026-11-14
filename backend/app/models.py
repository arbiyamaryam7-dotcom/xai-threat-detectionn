"""Database tables: every analysed flow (Prediction) and the alerts raised from them."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    destination_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    predicted_class: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    anomaly_score: Mapped[float] = mapped_column(Float)
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    true_label: Mapped[str | None] = mapped_column(String(32), nullable=True)  # only for simulated/labelled data
    features: Mapped[dict] = mapped_column(JSON)
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    alert: Mapped[Optional["Alert"]] = relationship(back_populates="prediction", uselist=False)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id", ondelete="CASCADE"), index=True)
    severity: Mapped[str] = mapped_column(String(10))               # low | medium | high
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)  # open | acknowledged | resolved | false_positive
    message: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    prediction: Mapped[Prediction] = relationship(back_populates="alert")
