"""
Model Router - Intelligent routing to multiple LLM models.

Routes requests to Claude, GPT-4, or local models based on:
- Model availability
- Cost optimization
- Latency requirements
- Failover logic
"""

import logging
import time
from typing import Dict, List

import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelResponse(BaseModel):
    """Response from LLM model with validation"""
    content: str = Field(..., description="Generated content from model")
    tokens_used: int = Field(..., ge=0, description="Total tokens used (input + output)")
    cost: float = Field(..., ge=0.0, description="Cost in USD")
    latency_ms: int = Field(0, ge=0, description="Response latency in milliseconds")
    model: str = Field(..., description="Model name used")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Hello, how can I help you?",
                "tokens_used": 150,
                "cost": 0.0045,
                "latency_ms": 1234,
                "model": "claude-3-sonnet"
            }
        }


class ModelRouter:
    """
    Multi-model router with intelligent routing logic.

    Supports:
    - Claude (Anthropic)
    - GPT-4 (OpenAI)
    - Local models (Ollama)
    """

    def __init__(self):
        """Initialize model router"""
        # TODO: Load API keys from environment
        self.claude_client = AsyncAnthropic(api_key="dummy_key")
        self.openai_client = AsyncOpenAI(api_key="dummy_key")
        self.local_model_url = "http://localhost:11434"  # Ollama

        # Pricing (USD per 1M tokens)
        self.pricing = {
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-opus": {"input": 15.0, "output": 75.0},
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "local": {"input": 0.0, "output": 0.0},  # Free
        }

        logger.info("ModelRouter initialized")

    async def route(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> ModelResponse:
        """
        Route request to appropriate model.

        Args:
            model: Model name
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            ModelResponse with completion
        """
        start_time = time.time()

        try:
            if model.startswith("claude"):
                response = await self._call_claude(model, messages, temperature, max_tokens)
            elif model.startswith("gpt"):
                response = await self._call_openai(model, messages, temperature, max_tokens)
            elif model == "local":
                response = await self._call_local(messages, temperature, max_tokens)
            else:
                raise ValueError(f"Unknown model: {model}")

            latency_ms = int((time.time() - start_time) * 1000)
            response.latency_ms = latency_ms

            logger.info(
                f"Model {model} responded in {latency_ms}ms, "
                f"tokens={response.tokens_used}, cost=${response.cost:.4f}"
            )

            return response

        except Exception as e:
            logger.error(f"Error routing to model {model}: {e}")
            # Try fallback model
            if model != "gpt-3.5-turbo":
                logger.info(f"Falling back to gpt-3.5-turbo from {model}")
                return await self.route("gpt-3.5-turbo", messages, temperature, max_tokens)
            raise

    async def _call_claude(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ModelResponse:
        """Call Claude API"""
        try:
            response = await self.claude_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )

            content = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            cost = self._calculate_cost(model, input_tokens, output_tokens)

            return ModelResponse(
                content=content,
                tokens_used=input_tokens + output_tokens,
                cost=cost,
                latency_ms=0,  # Set by caller
                model=model,
            )

        except Exception as e:
            logger.error(f"Error calling Claude: {e}")
            raise

    async def _call_openai(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ModelResponse:
        """Call OpenAI API"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            cost = self._calculate_cost(model, input_tokens, output_tokens)

            return ModelResponse(
                content=content,
                tokens_used=input_tokens + output_tokens,
                cost=cost,
                latency_ms=0,
                model=model,
            )

        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}")
            raise

    async def _call_local(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> ModelResponse:
        """Call local model (Ollama)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.local_model_url}/api/chat",
                    json={
                        "model": "llama2",
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    timeout=60.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("message", {}).get("content", "")

                    return ModelResponse(
                        content=content,
                        tokens_used=len(content.split()),  # Approximation
                        cost=0.0,  # Local model is free
                        latency_ms=0,
                        model="local",
                    )
                else:
                    raise Exception(f"Local model error: {response.status_code}")

        except Exception as e:
            logger.error(f"Error calling local model: {e}")
            raise

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate API call cost.

        Args:
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count

        Returns:
            Cost in USD
        """
        if model not in self.pricing:
            return 0.0

        pricing = self.pricing[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
