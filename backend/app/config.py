from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    fireworks_api_key: str = ""
    fireworks_model: str = "accounts/fireworks/models/gpt-oss-120b"
    demo_data_dir: Path = Path(__file__).resolve().parents[2] / "data" / "demo"
    test_data_dir: Path = Path(__file__).resolve().parents[2] / "data" / "test"
    inference_mode: str = "stub"  # stub | docker
    xview2_docker_image: str = "darknem-xview2-inference"
    upload_dir: Path = Path(__file__).resolve().parents[1] / "uploads"
    output_dir: Path = Path(__file__).resolve().parents[1] / "outputs"
    grid_rows: int = 4
    grid_cols: int = 4
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Endpoint protection. Both are opt-in so the demo works out of the box.
    # access_token: if set, the expensive endpoints require a matching X-API-Key
    #   header (useful only when the backend is called server-side or via a
    #   proxy — a browser-facing token would be exposed to clients).
    # rate_limit_requests per rate_limit_window_seconds, per client IP. Set the
    #   request count to 0 to disable rate limiting.
    access_token: str = ""
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
