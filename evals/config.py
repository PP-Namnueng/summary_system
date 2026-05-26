"""Shared local config loading for evaluation and LLM provider contracts."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CONFIG_PATH = PROJECT_ROOT / "config.example.yaml"
LOCAL_CONFIG_PATH = PROJECT_ROOT / "config.local.yaml"


DEFAULT_CONFIG: dict[str, Any] = {
    "app": {
        "debug": False,
    },
    "llm": {
        "generator": {
            "provider": "ollama",
            "model_source": "streamlit_select",
            "base_url": "http://localhost:11434",
            "max_concurrency": 1,
            "timeout_seconds": 120,
        },
        "gemini": {
            "enabled": False,
            "api_key_env": "GEMINI_API_KEY",
        },
        "openrouter": {
            "enabled": False,
            "api_key_env": "OPENROUTER_API_KEY",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "openai/gpt-4.1-nano",
            "site_url": None,
            "app_name": "summary",
        },
    },
    "eval": {
        "enabled": False,
        "mode": "off",
        "ragas": {
            "enabled": False,
            "run_mode": "offline_only",
            "judge": {
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "fallback_provider": "ollama",
                "ollama_model": None,
                "embeddings_provider": "ollama",
                "ollama_embedding_model": None,
                "max_workers": 1,
                "max_retries": 1,
                "timeout_seconds": 180,
                "max_wait_seconds": 60,
                "allow_external": False,
            },
            "thresholds": {
                "faithfulness": 0.80,
                "context_precision": 0.70,
                "answer_relevancy": 0.75,
                "context_recall": 0.70,
            },
        },
        "deepeval": {
            "enabled": False,
            "judge": {
                "provider": "gemini",
                "model": "gemini-2.0-flash",
                "fallback_provider": "ollama",
                "allow_external": False,
                "max_calls_per_run": 1,
                "combined_rubric": True,
            },
            "thresholds": {
                "summary_quality": 0.80,
                "factuality": 0.85,
                "coverage": 0.75,
                "conciseness": 0.70,
                "relevance": 0.75,
                "format_correctness": 1.00,
            },
        },
        "behavior": {
            "fail_mode": "warn",
            "fallback_response": "The summary did not pass the configured quality check.",
            "max_regenerate_attempts": 1,
            "max_retrieve_attempts": 1,
        },
    },
    "rag": {
        "top_k": 5,
        "min_similarity": 0.72,
        "min_top_similarity": 0.72,
        "min_avg_similarity": 0.60,
        "min_context_count": 2,
        "max_duplicate_ratio": 0.35,
        "fallback_response": "I could not find enough reliable context in your library to answer this question.",
        "enable_auto_retrieve": False,
        "max_attempts": 1,
        "retry_strategies": ["increase_top_k"],
        "increase_top_k": {
            "increment": 3,
            "max_top_k": 15,
        },
        "content_quality": {
            "enabled": True,
            "mode": "downrank",
            "penalty": 0.2,
            "patterns": [
                r"^\s*table of contents\b",
                r"^\s*contents\b",
                r"^\s*praise for\b",
                r"^\s*copyright\b",
                r"^\s*index\b",
                r"^\s*references\b",
                r"^\s*bibliography\b",
                r"^\s*about the author\b",
            ],
        },
        "keyword_search": {
            "provider": "in_memory_bm25",
            "input_source": "lancedb",
            "top_k": 20,
            "min_score": None,
            "rebuild_on_startup": False,
            "cache_path": "library/data/keyword_index",
            "max_chunks_for_in_memory": 50000,
            "fields": {
                "text_weight": 1.0,
                "title_weight": 2.0,
                "chapter_weight": 1.5,
            },
        },
        "hybrid_search": {
            "enabled": False,
            "vector_top_k": 20,
            "keyword_top_k": 20,
            "final_top_k": 8,
            "merge_strategy": "rrf",
            "rrf_k": 60,
            "vector_weight": 1.0,
            "keyword_weight": 1.0,
        },
        "reranker": {
            "enabled": False,
            "provider": "local",
            "model": "BAAI/bge-reranker-v2-m3",
            "device": "auto",
            "input_top_n": 15,
            "final_top_k": 6,
            "max_pair_tokens": 512,
            "batch_size": 4,
            "min_rerank_score": None,
            "fail_open": True,
        },
        "enable_query_rewrite": False,
        "query_rewrite": {
            "provider": "gemini",
            "fallback_provider": "ollama",
            "trigger": "retrieval_gate_failed",
        },
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "YAML config support requires PyYAML. Install project dependencies or add PyYAML."
        ) from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a YAML mapping at the top level.")

    return data


def load_eval_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load defaults merged with config.local.yaml or an explicit config path.

    Defaults keep evaluation disabled. `config.local.yaml` is optional and is
    intended for local model choices, evaluator thresholds, and API settings.
    `config.example.yaml` is documentation only and is not loaded at runtime.
    """
    config = deepcopy(DEFAULT_CONFIG)

    path = Path(config_path) if config_path else LOCAL_CONFIG_PATH
    config = _deep_merge(config, _read_yaml(path))

    if config.get("eval", {}).get("mode") is False:
        config["eval"]["mode"] = "off"

    return config


def get_config_value(config: dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    current: Any = config
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
