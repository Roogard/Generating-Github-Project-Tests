"""LLM provider plumbing.

`build_config` and `get_llm` are the only public API. Test-generation logic
lives in `src/skills/` — each skill calls `get_llm(cfg).invoke(messages)` once
per invocation (no tool binding; the harness owns dispatch).
"""
import os

_PROVIDERS = {
    "deepseek":  {"base_url": "https://api.deepseek.com",       "api_key_env": "DEEPSEEK_API_KEY"},
    "openai":    {"base_url": "https://api.openai.com/v1",       "api_key_env": "OPENAI_API_KEY"},
    "anthropic": {"base_url": "",                                 "api_key_env": "ANTHROPIC_API_KEY"},
    "ollama":    {"base_url": "http://localhost:11434/v1",        "api_key_env": ""},
}
_DEFAULT_MODELS = {
    "deepseek": "deepseek-chat", "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-6", "ollama": "llama3.2",
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
