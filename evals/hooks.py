"""No-op integration hooks for future Retry Retrieve, DeepEval, and RAGAS work."""

from __future__ import annotations

from typing import Any


def should_run_runtime_summary_eval(config: dict[str, Any]) -> bool:
    eval_config = config.get("eval", {})
    return bool(eval_config.get("enabled")) and eval_config.get("mode") in {"lightweight", "full"}


def prepare_retry_retrieve_input(trace: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace": trace,
        "rag_config": config.get("rag", {}),
        "behavior": config.get("eval", {}).get("behavior", {}),
    }


def prepare_deepeval_input(trace: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace": trace,
        "deepeval_config": config.get("eval", {}).get("deepeval", {}),
        "behavior": config.get("eval", {}).get("behavior", {}),
    }


def prepare_ragas_input(trace: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace": trace,
        "ragas_config": config.get("eval", {}).get("ragas", {}),
        "run_mode": config.get("eval", {}).get("ragas", {}).get("run_mode", "offline_only"),
    }
