import os
import tomllib


DEFAULTS = {

    #I found deepseek to be the best llm here, since it's solid at coding and very cheap

    "llm": {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "base_url": "",
        "api_key_env": "DEEPSEEK_API_KEY",
    },

    #project isn't a proper harness yet, but it will be

    "harness": {
        "quality_threshold": 0.80,
        "max_steps": 20,
        "max_fix_attempts": 2,
        "test_types": [],
    },

    #separate config for the llm supervisor — empty strings fall back to llm section
    "supervisor": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "temperature": 0.0,
    },

    #safety since some of these can take a long time

    "timeouts": {
        "test": 60,
        "coverage": 120,
        "mutmut": 600,
        "custom_mutant": 10,
    },
}

PROVIDER_DEFAULTS = {
    "deepseek": {"base_url": "https://api.deepseek.com", "api_key_env": "DEEPSEEK_API_KEY"},
    "openai": {"base_url": "https://api.openai.com/v1", "api_key_env": "OPENAI_API_KEY"},
    "anthropic": {"base_url": "", "api_key_env": "ANTHROPIC_API_KEY"},
    "ollama": {"base_url": "http://localhost:11434/v1", "api_key_env": ""},
}

ENV_OVERRIDES = {
    "LLM_PROVIDER": ("llm", "provider"),
    "LLM_MODEL": ("llm", "model"),
    "LLM_BASE_URL": ("llm", "base_url"),
    "QUALITY_THRESHOLD": ("harness", "quality_threshold"),
    "MAX_STEPS": ("harness", "max_steps"),
    "MAX_FIX_ATTEMPTS": ("harness", "max_fix_attempts"),
    "TIMEOUT_TEST": ("timeouts", "test"),
    "TIMEOUT_COVERAGE": ("timeouts", "coverage"),
    "TIMEOUT_MUTMUT": ("timeouts", "mutmut"),
    "TIMEOUT_CUSTOM_MUTANT": ("timeouts", "custom_mutant"),
    "SUPERVISOR_PROVIDER": ("supervisor", "provider"),
    "SUPERVISOR_MODEL": ("supervisor", "model"),
    "SUPERVISOR_BASE_URL": ("supervisor", "base_url"),
}


def _deep_merge(base, override):
    merged = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def _apply_env_overrides(config):
    for env_key, (section, key) in ENV_OVERRIDES.items():
        val = os.environ.get(env_key)
        if val is None:
            continue
        expected_type = type(DEFAULTS[section][key])
        if expected_type is float:
            val = float(val)
        elif expected_type is int:
            val = int(val)
        elif expected_type is bool:
            val = val.lower() in ("1", "true", "yes")
        config[section][key] = val


def _apply_provider_defaults(config):
    provider = config["llm"]["provider"]
    if provider in PROVIDER_DEFAULTS:
        defaults = PROVIDER_DEFAULTS[provider]
        if not config["llm"]["base_url"]:
            config["llm"]["base_url"] = defaults["base_url"]
        if config["llm"]["api_key_env"] == DEFAULTS["llm"]["api_key_env"] and provider != "deepseek":
            config["llm"]["api_key_env"] = defaults["api_key_env"]


def load_config(cli_overrides=None):
    config = {k: dict(v) for k, v in DEFAULTS.items()}

    for toml_path in ["ghtest.toml", os.path.join(os.path.dirname(os.path.dirname(__file__)), "ghtest.toml")]:
        if os.path.exists(toml_path):
            with open(toml_path, "rb") as f:
                file_config = tomllib.load(f)
            config = _deep_merge(config, file_config)
            break

    _apply_env_overrides(config)

    if cli_overrides:
        config = _deep_merge(config, cli_overrides)

    _apply_provider_defaults(config)

    return config
