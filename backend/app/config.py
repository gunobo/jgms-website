from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://jgms:jgms_dev_pw@localhost:3306/jgms_club"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    google_client_id: str = ""
    google_workspace_hd: str = ""

    admin_emails: str = ""

    google_service_account_email: str = ""
    google_service_account_private_key: str = ""

    frontend_origin: str = "http://localhost:5173"
    cookie_secure: bool = False

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip() for e in self.admin_emails.split(",") if e.strip()]


settings = Settings()
