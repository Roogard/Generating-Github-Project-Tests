"""LLM provider plumbing.

`build_config`, `get_llm`, and `cached_system_message` are the public API.
Test-generation logic lives in `src/skills/` — each skill calls
`get_llm(cfg).invoke(messages)` once per invocation (no tool binding; the
harness owns dispatch).
"""
import os

from langchain_core.messages import SystemMessage

_PROVIDERS = {
    "deepseek":  {"base_url": "https://api.deepseek.com",       "api_key_env": "DEEPSEEK_API_KEY"},
    "openai":    {"base_url": "https://api.openai.com/v1",       "api_key_env": "OPENAI_API_KEY"},
    "anthropic": {"base_url": "",                                 "api_key_env": "ANTHROPIC_API_KEY"},
    "ollama":    {"base_url": "http://localhost:11434/v1",        "api_key_env": ""},
}
_DEFAULT_MODELS = {
    "deepseek": "deepseek-chat", "openai": "gpt-4o",
    "anthropic": "claude-haiku-4-5", "ollama": "llama3.2",
}

_LLM_TIMEOUT = 120  # seconds — prevents LLM API calls from hanging indefinitely


def build_config(provider: str, model: str | None = None, api_key: str | None = None) -> dict:
    p = _PROVIDERS.get(provider, _PROVIDERS["deepseek"])
    return {
        "provider": provider,
        "model": model or _DEFAULT_MODELS.get(provider, "deepseek-chat"),
        "base_url": os.environ.get("LLM_BASE_URL", p["base_url"]),
        "api_key": api_key or (os.environ.get(p["api_key_env"], "") if p["api_key_env"] else ""),
    }


def get_llm(cfg: dict):
    if cfg["provider"] == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=cfg["model"], api_key=cfg["api_key"], timeout=_LLM_TIMEOUT)
    from langchain_openai import ChatOpenAI
    kwargs: dict = {"model": cfg["model"], "timeout": _LLM_TIMEOUT}
    if cfg["api_key"]:
        kwargs["api_key"] = cfg["api_key"]
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]
    return ChatOpenAI(**kwargs)


def cached_system_message(cfg: dict, text: str) -> SystemMessage:
    """SystemMessage that opts into Anthropic ephemeral prompt caching.

    For provider='anthropic' the system prompt is wrapped as a structured
    content block carrying `cache_control: ephemeral`. langchain_anthropic
    forwards the block as-is, so turn 2+ in a multi-turn loop pays ~0.1× the
    input rate for the system-prompt tokens (5-minute TTL). Other providers
    get a plain string SystemMessage — `cache_control` is Anthropic-only.

    Cacheable-prefix minimums apply: 2048 tokens on Sonnet 4.6, 4096 tokens
    on Haiku 4.5 / Opus 4.x. Below the minimum the API silently skips
    caching (no error, just `cache_read_input_tokens=0`). Verify hits via
    `response.usage_metadata` after the second turn of any loop.
    """
    if cfg.get("provider") == "anthropic":
        return SystemMessage(content=[{
            "type": "text",
            "text": text,
            "cache_control": {"type": "ephemeral"},
        }])
    return SystemMessage(content=text)
