"""Builds the chat model behind the AI assistant for whichever
provider is configured (settings.chat_model_provider) -- one factory
function so provider branching doesn't scatter across ai_agent.py/
ai_graph.py. This is also the module ai_agent.py's "is this provider
set up" guard lives in: each case raises a clear RuntimeError for a
missing key rather than letting the provider SDK's own (less
helpful) error surface.

Ollama's tool-calling is best-effort only compared to Anthropic/OpenAI
-- it can emit malformed tool calls or skip one it should have made.
No special validation is added for that here; the agent's existing
system-prompt rule ("say so plainly rather than guessing") is the
only guardrail, same as for any other provider. See the README's
limitations section.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import settings

MAX_RESPONSE_TOKENS = 1024


def build_chat_model() -> BaseChatModel:
    match settings.chat_model_provider:
        case "anthropic":
            if not settings.anthropic_api_key:
                raise RuntimeError(
                    "No anthropic_api_key configured -- set one in .env to "
                    "use the AI assistant."
                )
            return ChatAnthropic(
                model=settings.ai_agent_model,
                api_key=settings.anthropic_api_key,
                max_tokens=MAX_RESPONSE_TOKENS,
            )
        case "openai":
            if not settings.openai_api_key:
                raise RuntimeError(
                    "No openai_api_key configured -- set one in .env to use "
                    "the AI assistant with chat_model_provider=openai."
                )
            return ChatOpenAI(
                model=settings.ai_agent_model,
                api_key=settings.openai_api_key,
                max_tokens=MAX_RESPONSE_TOKENS,
            )
        case "ollama":
            # No API key -- Ollama runs locally. If ollama_base_url is
            # unreachable, that surfaces as a connection error when the
            # model is actually invoked, not here.
            return ChatOllama(
                model=settings.ai_agent_model, base_url=settings.ollama_base_url
            )
        case other:
            raise RuntimeError(f"Unknown chat_model_provider: {other!r}")
