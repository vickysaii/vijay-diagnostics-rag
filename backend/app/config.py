from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://vijay_user:vijay_pass@localhost:5432/vijay_diagnostics"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Cosine distance threshold above which a retrieved chunk is considered
    # "not actually relevant" and gets filtered out (0 = identical meaning,
    # higher = less related). Tune this based on real queries - if relevant
    # answers are getting dropped, raise it slightly; if off-topic questions
    # are pulling in random chunks, lower it.
    MAX_RELEVANT_DISTANCE: float = 0.8
    APP_ENV: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
