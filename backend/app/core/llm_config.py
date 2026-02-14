"""LLM 配置模块 — 支持多模型切换与容错"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class LLMSettings(BaseSettings):
    """LLM 配置 — 支持 OpenAI / DeepSeek / Qwen 多模型"""

    # Primary provider
    LLM_PROVIDER: str = "deepseek"  # openai | deepseek | qwen

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Qwen (通义千问 — compatible with OpenAI API)
    QWEN_API_KEY: str = ""
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-plus"

    # Fallback provider (used when primary fails)
    LLM_FALLBACK_PROVIDER: str = ""  # leave empty to disable fallback

    # Generation defaults
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 4000

    # Retry
    LLM_MAX_RETRIES: int = 2
    LLM_TIMEOUT: int = 60  # seconds

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

    def get_provider_config(self, provider: Optional[str] = None) -> dict:
        """Return (api_key, base_url, model) for the given provider."""
        p = provider or self.LLM_PROVIDER
        if p == "openai":
            return {"api_key": self.OPENAI_API_KEY, "base_url": self.OPENAI_BASE_URL, "model": self.OPENAI_MODEL}
        elif p == "deepseek":
            return {"api_key": self.DEEPSEEK_API_KEY, "base_url": self.DEEPSEEK_BASE_URL, "model": self.DEEPSEEK_MODEL}
        elif p == "qwen":
            return {"api_key": self.QWEN_API_KEY, "base_url": self.QWEN_BASE_URL, "model": self.QWEN_MODEL}
        else:
            return {"api_key": self.OPENAI_API_KEY, "base_url": self.OPENAI_BASE_URL, "model": self.OPENAI_MODEL}

