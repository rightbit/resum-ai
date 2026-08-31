"""AI provider abstraction.

The application should not be tightly coupled to a single AI vendor. This
module defines a small `AIProvider` interface and an
`OpenAICompatibleProvider` implementation that works with any API that
speaks the OpenAI chat-completions protocol (OpenAI itself, Azure OpenAI
compatible gateways, local proxies such as LiteLLM/Ollama's OpenAI-shim,
etc.) configured purely through environment variables.

Swapping providers in the future (e.g. Anthropic, a local model) should
only require adding a new class that implements `AIProvider` and wiring
it up in `get_ai_provider()`.
"""
from __future__ import annotations

import abc

from openai import OpenAI

from app.config import settings

NO_ANSWER_MESSAGE = (
    f"I don't have enough information in {settings.PROFILE_OWNER_NAME}'s "
    "professional profile to answer that accurately."
)

SYSTEM_PROMPT_TEMPLATE = """You are an AI assistant that answers questions about \
{owner}'s professional background, on behalf of {owner}, for recruiters, hiring \
managers, and other professional contacts.

STRICT RULES:
- Only use information present in the "PROFESSIONAL CONTEXT" section below.
- Never invent experience, technologies, responsibilities, dates, employers, \
or accomplishments that are not directly supported by the provided context.
- If the context does not contain enough information to answer confidently, \
respond with exactly: "{no_answer}"
- Do not speculate about what {owner} "probably" did or "might have" done.
- Answer in a professional, concise, third-person tone (e.g. "Ryan led...").
- You may synthesize/summarize across multiple provided facts, but every \
claim must be traceable to the provided context.

PROFESSIONAL CONTEXT:
{context}
"""


class AIProvider(abc.ABC):
    """Interface all AI providers must implement."""

    @abc.abstractmethod
    def generate_answer(
        self,
        question: str,
        context: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Return an answer string for the given question and context."""

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        ...


class OpenAICompatibleProvider(AIProvider):
    """AI provider backed by any OpenAI-compatible chat completions API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self._model = model or settings.AI_MODEL
        self._client = OpenAI(
            api_key=api_key or settings.AI_API_KEY or "unset",
            base_url=base_url or settings.AI_API_BASE_URL,
        )

    @property
    def model_name(self) -> str:
        return self._model

    def generate_answer(
        self,
        question: str,
        context: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            owner=settings.PROFILE_OWNER_NAME,
            no_answer=NO_ANSWER_MESSAGE,
            context=context or "(no relevant professional context found)",
        )
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for turn in (history or [])[-6:]:
            messages.append(turn)
        messages.append({"role": "user", "content": question})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return (content or "").strip() or NO_ANSWER_MESSAGE


def get_ai_provider() -> AIProvider:
    """Factory returning the configured AI provider.

    Centralizing provider selection here means adding a new provider only
    requires updating this function (and adding the class above), not any
    calling code.
    """
    return OpenAICompatibleProvider()
