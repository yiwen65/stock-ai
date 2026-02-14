"""LLM 服务模块 — 多模型支持 + 容错 + Token 统计"""

import json
import time
import logging
from openai import AsyncOpenAI
from typing import List, Dict, Optional

from app.core.llm_config import LLMSettings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 服务 — 支持 OpenAI / DeepSeek / Qwen 多模型自动切换"""

    def __init__(self, settings: Optional[LLMSettings] = None):
        self.settings = settings or LLMSettings()
        self.temperature = self.settings.OPENAI_TEMPERATURE
        self.max_tokens = self.settings.OPENAI_MAX_TOKENS

        # Build primary client
        primary = self.settings.get_provider_config()
        self.primary_model = primary["model"]
        self.primary_client = self._build_client(primary)

        # Build fallback client (optional)
        self.fallback_client = None
        self.fallback_model = None
        if self.settings.LLM_FALLBACK_PROVIDER:
            fallback = self.settings.get_provider_config(self.settings.LLM_FALLBACK_PROVIDER)
            self.fallback_model = fallback["model"]
            self.fallback_client = self._build_client(fallback)

        # Token usage tracking
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_calls = 0
        self._total_errors = 0

    @staticmethod
    def _build_client(cfg: dict) -> Optional[AsyncOpenAI]:
        if not cfg.get("api_key"):
            return None
        return AsyncOpenAI(
            api_key=cfg["api_key"],
            base_url=cfg.get("base_url"),
            timeout=60.0,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Call LLM with automatic primary → fallback switching."""
        temp = temperature if temperature is not None else self.temperature
        mtokens = max_tokens or self.max_tokens

        # Try primary
        result = await self._try_call(
            self.primary_client, self.primary_model, messages, temp, mtokens, label="primary"
        )
        if result is not None:
            return result

        # Try fallback
        if self.fallback_client:
            logger.warning("Primary LLM failed, trying fallback...")
            result = await self._try_call(
                self.fallback_client, self.fallback_model, messages, temp, mtokens, label="fallback"
            )
            if result is not None:
                return result

        self._total_errors += 1
        raise RuntimeError("All LLM providers failed")

    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict] = None,
    ) -> Dict:
        """Call LLM and parse JSON response."""
        # Append instruction to return JSON
        json_messages = list(messages)
        if json_messages and json_messages[-1]["role"] == "user":
            json_messages[-1] = {
                **json_messages[-1],
                "content": json_messages[-1]["content"] + "\n\n请以 JSON 格式返回结果。",
            }

        raw = await self.chat_completion(json_messages, temperature=0.3)

        # Try to extract JSON from response
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to find JSON block in markdown
            import re
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # Last resort: wrap as dict
            return {"raw_response": raw}

    def get_usage_stats(self) -> Dict:
        """Return cumulative token usage statistics."""
        return {
            "total_calls": self._total_calls,
            "total_errors": self._total_errors,
            "total_prompt_tokens": self._total_prompt_tokens,
            "total_completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
            "provider": self.settings.LLM_PROVIDER,
            "model": self.primary_model,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    async def _try_call(
        self,
        client: Optional[AsyncOpenAI],
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        label: str = "",
    ) -> Optional[str]:
        if client is None:
            return None

        retries = self.settings.LLM_MAX_RETRIES
        for attempt in range(1, retries + 1):
            try:
                t0 = time.time()
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                elapsed = time.time() - t0

                # Track usage
                self._total_calls += 1
                usage = response.usage
                if usage:
                    self._total_prompt_tokens += usage.prompt_tokens
                    self._total_completion_tokens += usage.completion_tokens

                content = response.choices[0].message.content
                logger.info(
                    f"LLM [{label}/{model}] OK in {elapsed:.1f}s "
                    f"(tokens: {usage.total_tokens if usage else '?'})"
                )
                return content
            except Exception as e:
                logger.warning(f"LLM [{label}/{model}] attempt {attempt}/{retries} failed: {e}")
                if attempt < retries:
                    await self._sleep(attempt)

        return None

    @staticmethod
    async def _sleep(attempt: int):
        import asyncio
        await asyncio.sleep(min(2 ** attempt, 10))
