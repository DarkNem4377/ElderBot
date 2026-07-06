from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    fireworks_api_key: str = ""
    fireworks_model: str = "accounts/fireworks/models/llama-v3p1-8b-instruct"
    demo_data_dir: Path = Path(__file__).resolve().parents[2] / "data" / "demo"
    test_data_dir: Path = Path(__file__).resolve().parents[2] / "data" / "test"
    inference_mode: str = "stub"  # stub | docker
    xview2_docker_image: str = "darknem-xview2-inference"
    upload_dir: Path = Path(__file__).resolve().parents[1] / "uploads"
    output_dir: Path = Path(__file__).resolve().parents[1] / "outputs"
    grid_rows: int = 4
    grid_cols: int = 4
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
