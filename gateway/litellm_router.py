"""LiteLLM router with Granite→Gemini→Groq fallback and cost logging."""
import os
import litellm
from litellm import completion
from dotenv import load_dotenv
from gateway.cost_log import log_call

load_dotenv()
litellm.suppress_debug_info = True

# Model IDs can be overridden in .env if a provider retires one
GRANITE = os.environ.get("GRANITE_MODEL", "watsonx/ibm/granite-4-h-small")
GEMINI = os.environ.get("GEMINI_MODEL", "gemini/gemini-3.5-flash")
GROQ = os.environ.get("GROQ_MODEL", "groq/llama-3.1-8b-instant")

FALLBACK_ORDER = [GRANITE, GEMINI, GROQ]

_KEY_ENV = {"watsonx/": "WATSONX_API_KEY", "gemini/": "GEMINI_API_KEY", "groq/": "GROQ_API_KEY"}


def _has_key(model: str) -> bool:
    """Skip providers whose key is missing or still the .env.example placeholder."""
    for prefix, env in _KEY_ENV.items():
        if model.startswith(prefix):
            key = os.environ.get(env, "")
            return bool(key) and not key.startswith("your_")
    return True


def _extra_kwargs(model: str) -> dict:
    """Return extra litellm kwargs required for watsonx models."""
    if model.startswith("watsonx/"):
        # LiteLLM wants the base URL only, not a full /ml/v1/... endpoint
        base = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").split("/ml/")[0]
        return {
            "api_base": base,
            "api_key": os.environ.get("WATSONX_API_KEY", ""),
            "project_id": os.environ.get("WATSONX_PROJECT_ID", ""),
        }
    if model.startswith("gemini/"):
        # Gemini thinking models spend output tokens on reasoning; keep it short
        return {"reasoning_effort": "low"}
    return {}


def _is_bad_response(resp) -> bool:
    """Return True if the response should be treated as a failure."""
    choice = resp.choices[0] if resp.choices else None
    if choice is None:
        return True
    content = choice.message.content or ""
    finish = getattr(choice, "finish_reason", None)
    if not content or content.lstrip().startswith("[ERROR"):
        return True
    if finish == "length":
        return True
    return False


def complete(agent_name: str, model: str, messages: list[dict], max_tokens: int = 1024) -> str:
    """Call LiteLLM with automatic fallback. Returns content string."""
    # Build ordered list: preferred model first, then remaining fallbacks
    order = [m for m in [model] + [m for m in FALLBACK_ORDER if m != model] if _has_key(m)]
    errors: list[str] = []
    for m in order:
        try:
            resp = completion(model=m, messages=messages, max_tokens=max_tokens,
                              **_extra_kwargs(m))
            if _is_bad_response(resp):
                errors.append(f"{m}: bad response (empty/error/length-truncated)")
                continue
            usage = dict(resp.usage) if resp.usage else {}
            log_call(agent_name, m, usage)
            return resp.choices[0].message.content
        except Exception as exc:
            errors.append(f"{m}: {type(exc).__name__}: {str(exc)[:200]}")
    detail = " | ".join(errors) or "no provider has an API key set in .env"
    raise RuntimeError(f"All LLM models exhausted for agent '{agent_name}': {detail}")
