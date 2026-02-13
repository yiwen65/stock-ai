"""LLM 配置模块"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class LLMSettings(BaseSettings):
    """LLM 配置"""

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2000

    # DeepSeek 配置（备选）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )

