from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)
    app_env: str = "development"
    bot_token: SecretStr = SecretStr("")
    admin_ids: list[int] = []
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://services:change-me@localhost/services"
    )
    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")
    telegram_mode: str = "polling"
    telegram_api_environment: Literal["production", "test"] = "production"
    miniapp_url: str = ""
    miniapp_bot_username: str = ""
    miniapp_intake_enabled: bool = False
    miniapp_confirm_enabled: bool = False
    publications_enabled: bool = False
    publication_origin: str = ""
    publication_terms_version: str = ""
    publication_terms_ar: str = ""
    publication_terms_en: str = ""
    telegram_webhook_secret: SecretStr = SecretStr("")
    stars_enabled: bool = False
    stars_terms_version: str = ""
    stars_terms_ar: str = ""
    stars_terms_en: str = ""
    ai_provider: str = "openai_compatible"
    ai_api_key: SecretStr = SecretStr("")
    ai_base_url: str = "https://api.openai.com/v1"
    ai_image_token_bound: int = 20000
    ai_max_output_tokens: int = 8192
    ai_token_limit_parameter: Literal["auto", "max_tokens", "max_completion_tokens"] = "auto"
    ai_deepseek_thinking: Literal["disabled", "enabled"] = "disabled"
    ai_model: str = "gpt-4.1-mini"
    ai_enabled: bool = False
    document_visual_review: bool = False
    ai_input_usd_per_million: Decimal = Decimal("0")
    ai_output_usd_per_million: Decimal = Decimal("0")
    usd_to_sar: Decimal = Decimal("3.75")
    max_daily_cost_sar: Decimal = Decimal("50")
    max_cost_per_user_per_day: Decimal = Decimal("10")
    max_concurrent_jobs_per_user: int = 2
    max_job_cost_sar: Decimal = Decimal("2")
    provider_low_balance_sar: Decimal = Decimal("10")
    failure_alert_count: int = 3
    circuit_window: int = 10
    circuit_min_samples: int = 5
    circuit_failure_threshold: float = 0.6
    max_attempts: int = 3
    report_hour: int = 23
    report_minute: int = 0
    file_ttl_hours: int = 24
    max_file_bytes: int = 10485760
    storage_quota_bytes: int = 52428800
    storage_quota_files: int = 100
    storage_root: Path = Path("data/files")

    @model_validator(mode="after")
    def validate_config(self):
        if self.stars_enabled and (
            self.telegram_mode != "webhook"
            or not 1 <= len(self.stars_terms_version) <= 80
            or not self.stars_terms_version.strip()
            or any(
                not 20 <= len(text) <= 2500 for text in (self.stars_terms_ar, self.stars_terms_en)
            )
            or any(
                len(text.encode("utf-16-le")) // 2 > 2500 or not text.strip()
                for text in (self.stars_terms_ar, self.stars_terms_en)
            )
        ):
            raise ValueError("Stars requires authenticated webhook mode and configured terms")
        if self.telegram_mode not in {"polling", "webhook"}:
            raise ValueError("invalid Telegram mode")
        if self.telegram_mode == "webhook" and not self.telegram_webhook_secret.get_secret_value():
            raise ValueError("webhook mode requires a secret")
        if min(self.max_daily_cost_sar, self.max_cost_per_user_per_day, self.max_job_cost_sar) <= 0:
            raise ValueError("cost limits must be positive")
        if (
            min(
                self.file_ttl_hours,
                self.max_attempts,
                self.max_file_bytes,
                self.max_concurrent_jobs_per_user,
                self.ai_image_token_bound,
                self.ai_max_output_tokens,
                self.failure_alert_count,
                self.circuit_window,
                self.circuit_min_samples,
                self.storage_quota_bytes,
                self.storage_quota_files,
            )
            < 1
        ):
            raise ValueError("limits must be positive")
        if (
            self.circuit_min_samples > self.circuit_window
            or not 0 < self.circuit_failure_threshold <= 1
        ):
            raise ValueError("invalid circuit settings")
        if self.ai_max_output_tokens > 32768:
            raise ValueError("AI output bound exceeds supported maximum")
        if (
            min(self.ai_input_usd_per_million, self.ai_output_usd_per_million) < 0
            or self.usd_to_sar <= 0
        ):
            raise ValueError("invalid provider rates")
        if self.ai_enabled and (
            not self.ai_api_key.get_secret_value()
            or min(self.ai_input_usd_per_million, self.ai_output_usd_per_million) <= 0
        ):
            raise ValueError("AI activation requires a key and positive rates")
        if len(set(self.admin_ids)) != len(self.admin_ids) or any(
            value <= 0 for value in self.admin_ids
        ):
            raise ValueError("administrator IDs must be positive and unique")
        from urllib.parse import urlsplit

        if self.publications_enabled:
            HttpUrl(self.publication_origin)
            origin = urlsplit(self.publication_origin)
            if (
                not self.miniapp_intake_enabled
                or not self.bot_token.get_secret_value()
                or origin.scheme != "https"
                or not origin.hostname
                or origin.username is not None
                or origin.password is not None
                or self.publication_origin
                not in {f"https://{origin.netloc}", f"https://{origin.netloc}/"}
                or len(self.publication_origin) > 220
                or any(
                    c.isspace()
                    or ord(c) < 32
                    or ord(c) == 127
                    or 0x202A <= ord(c) <= 0x202E
                    or 0x2066 <= ord(c) <= 0x2069
                    for c in self.publication_origin
                )
                or "\\" in self.publication_origin
                or not 1 <= len(self.publication_terms_version) <= 80
                or not self.publication_terms_version.strip()
                or any(
                    not 20 <= len(value) <= 2500 or not value.strip()
                    for value in (self.publication_terms_ar, self.publication_terms_en)
                )
            ):
                raise ValueError(
                    "Publication activation requires HTTPS origin, Mini App authentication and explicit bilingual terms"
                )

        if self.miniapp_bot_username:
            import re

            if not re.fullmatch(r"(?i:[a-z][a-z0-9_]{1,28}bot)", self.miniapp_bot_username):
                raise ValueError("Mini App bot username must be a plain bot username")
        if self.miniapp_url:
            web_app = urlsplit(self.miniapp_url)
            if (
                web_app.scheme != "https"
                or not web_app.hostname
                or web_app.username
                or web_app.password
                or web_app.query
                or web_app.fragment
                or web_app.path.rstrip("/") != "/miniapp"
            ):
                raise ValueError("Mini App requires a plain HTTPS /miniapp URL")
        endpoint = urlsplit(self.ai_base_url)
        if (
            endpoint.scheme not in {"https", "http"}
            or not endpoint.hostname
            or endpoint.username
            or endpoint.password
        ):
            raise ValueError("invalid AI endpoint")
        if self.ai_enabled and endpoint.scheme != "https":
            raise ValueError("AI activation requires an HTTPS endpoint")
        if not 0 <= self.report_hour <= 23 or not 0 <= self.report_minute <= 59:
            raise ValueError("invalid report time")
        return self


@lru_cache
def config() -> Config:
    return Config()
