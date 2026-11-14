"""Application settings, read from environment variables or the project-root .env file."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")
    database_url: str = "postgresql+psycopg2://xai_user:xai_pass@localhost:5432/xai_threat"
    anomaly_model: str = "autoencoder"          # autoencoder | isolation_forest
    anomaly_alert_threshold: float = 70.0       # 0-100 score above which Benign flows raise a low alert
    simulation_csv: str = str(ROOT / "data" / "sample_traffic.csv")
    cors_origins: str = "http://localhost:5173"
    max_batch_rows: int = 2000


settings = Settings()
