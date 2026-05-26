"""Offline RAGAS evaluation over Streamlit pipeline traces.

This module only reads trace/dataset records and returns calibration reports.
It never retries retrieval, rewrites queries, blocks responses, or calls runtime
fallback policy.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DEFAULT_CONFIG, PROJECT_ROOT, get_config_value, load_eval_config


DEFAULT_METRICS = ("faithfulness", "answer_relevancy", "context_precision")
REFERENCE_METRICS = ("context_recall",)
DEFAULT_GOLDEN_DATASET = PROJECT_ROOT / "data" / "golden" / "ragas_cases.jsonl"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"
REQUIRED_CASE_FIELDS = ("question", "answer", "contexts")


class RagasOfflineOnlyError(ValueError):
    """Raised when RAGAS is configured for a runtime mode."""


def _deep_get(mapping: dict[str, Any], keys: tuple[str, ...], default: Any = "") -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def _context_text(context: dict[str, Any] | str) -> str:
    if isinstance(context, str):
        return context
    return str(context.get("text") or context.get("content") or "")


def _normalize_case(record: dict[str, Any], index: int) -> dict[str, Any]:
    trace = record.get("trace") if isinstance(record.get("trace"), dict) else record
    contexts = trace.get("contexts") or trace.get("retrieved_contexts") or []
    reference = (
        record.get("ground_truth")
        or record.get("reference")
        or trace.get("ground_truth")
        or trace.get("reference")
        or _deep_get(trace, ("metadata", "ground_truth"))
        or _deep_get(trace, ("metadata", "reference"))
    )

    case_id = (
        record.get("case_id")
        or trace.get("case_id")
        or _deep_get(trace, ("metadata", "case_id"))
        or trace.get("trace_id")
        or f"case-{index + 1}"
    )
    trace_id = trace.get("trace_id") or record.get("trace_id") or str(case_id)

    return {
        "case_id": str(case_id),
        "trace_id": str(trace_id),
        "question": trace.get("query") or trace.get("final_query") or record.get("question") or "",
        "answer": trace.get("summary") or trace.get("answer") or record.get("answer") or "",
        "contexts": [_context_text(context) for context in contexts if _context_text(context).strip()],
        "ground_truth": reference or "",
        "notes": record.get("notes") or _deep_get(trace, ("metadata", "notes")),
        "raw": record,
    }


def load_ragas_cases(path: str | Path) -> list[dict[str, Any]]:
    """Load trace or golden cases from JSON, JSONL, or a single trace file."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"RAGAS input file does not exist: {source}")

    if source.suffix.lower() == ".jsonl":
        records = []
        with source.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
    else:
        with source.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, list):
            records = loaded
        elif isinstance(loaded, dict) and isinstance(loaded.get("cases"), list):
            records = loaded["cases"]
        elif isinstance(loaded, dict) and isinstance(loaded.get("traces"), list):
            records = loaded["traces"]
        elif isinstance(loaded, dict):
            records = [loaded]
        else:
            raise ValueError("RAGAS input must be a JSON object, array, or JSONL records.")

    return [_normalize_case(record, index) for index, record in enumerate(records)]


def _metric_names_for_cases(cases: list[dict[str, Any]]) -> list[str]:
    metric_names = list(DEFAULT_METRICS)
    if cases and all(case.get("ground_truth") for case in cases):
        metric_names.extend(REFERENCE_METRICS)
    return metric_names


def _validate_case(case: dict[str, Any]) -> list[str]:
    failures = []
    if not str(case.get("question") or "").strip():
        failures.append("question")
    if not str(case.get("answer") or "").strip():
        failures.append("answer")
    if not case.get("contexts"):
        failures.append("contexts")
    return failures


def _safe_score(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _thresholds(config: dict[str, Any]) -> dict[str, float]:
    configured = get_config_value(config, "eval.ragas.thresholds", {})
    defaults = DEFAULT_CONFIG["eval"]["ragas"]["thresholds"]
    merged = {**defaults, **(configured or {})}
    return {key: float(value) for key, value in merged.items()}


def _empty_scores(metric_names: list[str], reason: str) -> dict[str, dict[str, Any]]:
    return {
        metric_name: {
            "score": None,
            "passed": None,
            "skipped": True,
            "reason": reason,
        }
        for metric_name in metric_names
    }


def _build_langchain_judge(config: dict[str, Any]) -> tuple[Any | None, Any | None, str | None]:
    ragas_config = get_config_value(config, "eval.ragas", {})
    judge = ragas_config.get("judge", {})
    provider = judge.get("provider", "gemini")
    provider_error = None

    api_key_env = get_config_value(config, "llm.gemini.api_key_env", "GEMINI_API_KEY")
    if provider == "gemini" and os.getenv(api_key_env):
        if not judge.get("allow_external", False):
            provider_error = (
                "Gemini judge is configured, but eval.ragas.judge.allow_external is false. "
                "Enable it only for traces safe to send to an external API."
            )
        else:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
            except ImportError:
                provider_error = "Gemini judge requested, but langchain-google-genai is not installed."
            else:
                return (
                    ChatGoogleGenerativeAI(model=judge.get("model") or "gemini-2.5-flash", temperature=0),
                    GoogleGenerativeAIEmbeddings(model="models/text-embedding-004"),
                    None,
                )
    elif provider == "gemini":
        provider_error = f"Gemini judge requested, but {api_key_env} is not configured."

    openrouter_key_env = get_config_value(config, "llm.openrouter.api_key_env", "OPENROUTER_API_KEY")
    if provider == "openrouter" and os.getenv(openrouter_key_env):
        if not judge.get("allow_external", False):
            provider_error = (
                "OpenRouter judge is configured, but eval.ragas.judge.allow_external is false. "
                "Enable it only for traces safe to send to an external API."
            )
        else:
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                provider_error = "OpenRouter judge requested, but langchain-openai is not installed."
            else:
                embeddings, embeddings_error = _build_ragas_embeddings(config, judge)
                if embeddings_error:
                    return None, None, embeddings_error
                return (
                    ChatOpenAI(
                        model=judge.get("model")
                        or get_config_value(config, "llm.openrouter.model", "openai/gpt-4.1-nano"),
                        base_url=get_config_value(
                            config,
                            "llm.openrouter.base_url",
                            "https://openrouter.ai/api/v1",
                        ),
                        api_key=os.getenv(openrouter_key_env),
                        temperature=0,
                    ),
                    embeddings,
                    None,
                )
    elif provider == "openrouter":
        provider_error = f"OpenRouter judge requested, but {openrouter_key_env} is not configured."

    fallback = judge.get("fallback_provider", "ollama")
    if fallback == "ollama" or provider == "ollama":
        try:
            from langchain_ollama import ChatOllama, OllamaEmbeddings
        except ImportError:
            message = "Ollama judge fallback requested, but langchain-ollama is not installed."
            return None, None, f"{provider_error} {message}".strip()

        model = judge.get("ollama_model") or get_config_value(config, "llm.generator.model") or "llama3.1"
        base_url = get_config_value(config, "llm.generator.base_url", "http://localhost:11434")
        return (
            ChatOllama(model=model, base_url=base_url, temperature=0),
            OllamaEmbeddings(model=model, base_url=base_url),
            None,
        )

    return None, None, provider_error or "No supported RAGAS judge provider is configured."


def _build_ragas_embeddings(config: dict[str, Any], judge: dict[str, Any]) -> tuple[Any | None, str | None]:
    embeddings_provider = judge.get("embeddings_provider", "ollama")
    if embeddings_provider == "ollama":
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError:
            return None, "Ollama embeddings requested, but langchain-ollama is not installed."

        model = judge.get("ollama_embedding_model") or judge.get("ollama_model") or get_config_value(
            config, "llm.generator.model"
        ) or "llama3.1"
        base_url = get_config_value(config, "llm.generator.base_url", "http://localhost:11434")
        return OllamaEmbeddings(model=model, base_url=base_url), None

    if embeddings_provider == "openai":
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            return None, "OpenAI embeddings requested, but langchain-openai is not installed."

        api_key_env = judge.get("embeddings_api_key_env", "OPENAI_API_KEY")
        if not os.getenv(api_key_env):
            return None, f"OpenAI embeddings requested, but {api_key_env} is not configured."
        return (
            OpenAIEmbeddings(
                model=judge.get("embeddings_model", "text-embedding-3-small"),
                api_key=os.getenv(api_key_env),
            ),
            None,
        )

    return None, f"Unsupported RAGAS embeddings provider: {embeddings_provider}"


def _import_ragas_metrics(metric_names: list[str]) -> tuple[Any | None, dict[str, Any], str | None]:
    try:
        from ragas import evaluate
        from ragas import metrics as ragas_metrics
    except ImportError:
        return None, {}, "ragas is not installed. Install the eval extra to run LLM-based metrics."

    metrics = {}
    for name in metric_names:
        metric = getattr(ragas_metrics, name, None)
        if metric is not None:
            metrics[name] = metric

    missing = sorted(set(metric_names) - set(metrics))
    if missing:
        return evaluate, metrics, f"Installed ragas package is missing metrics: {', '.join(missing)}"
    return evaluate, metrics, None


def _run_ragas(cases: list[dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    metric_names = _metric_names_for_cases(cases)
    evaluate, metric_map, import_error = _import_ragas_metrics(metric_names)
    if import_error or evaluate is None:
        rows = [
            {"case_id": case["case_id"], "trace_id": case["trace_id"], "scores": _empty_scores(metric_names, import_error or "RAGAS unavailable.")}
            for case in cases
        ]
        return rows, import_error

    llm, embeddings, provider_error = _build_langchain_judge(config)
    if provider_error or llm is None:
        rows = [
            {"case_id": case["case_id"], "trace_id": case["trace_id"], "scores": _empty_scores(metric_names, provider_error or "No judge available.")}
            for case in cases
        ]
        return rows, provider_error

    try:
        from datasets import Dataset
    except ImportError:
        rows = [
            {"case_id": case["case_id"], "trace_id": case["trace_id"], "scores": _empty_scores(metric_names, "datasets is not installed.")}
            for case in cases
        ]
        return rows, "datasets is not installed."

    dataset = Dataset.from_list(
        [
            {
                "question": case["question"],
                "answer": case["answer"],
                "contexts": case["contexts"],
                "ground_truth": case["ground_truth"] or None,
                "reference": case["ground_truth"] or None,
            }
            for case in cases
        ]
    )
    try:
        run_config = None
        max_workers = get_config_value(config, "eval.ragas.judge.max_workers")
        max_retries = get_config_value(config, "eval.ragas.judge.max_retries")
        timeout = get_config_value(config, "eval.ragas.judge.timeout_seconds")
        max_wait = get_config_value(config, "eval.ragas.judge.max_wait_seconds")
        if any(value is not None for value in (max_workers, max_retries, timeout, max_wait)):
            try:
                from ragas.run_config import RunConfig
            except ImportError:
                RunConfig = None
            if RunConfig is not None:
                kwargs = {}
                if max_workers is not None:
                    kwargs["max_workers"] = int(max_workers)
                if max_retries is not None:
                    kwargs["max_retries"] = int(max_retries)
                if timeout is not None:
                    kwargs["timeout"] = int(timeout)
                if max_wait is not None:
                    kwargs["max_wait"] = int(max_wait)
                run_config = RunConfig(**kwargs)

        evaluate_kwargs = {
            "dataset": dataset,
            "metrics": [metric_map[name] for name in metric_names],
            "llm": llm,
            "embeddings": embeddings,
            "raise_exceptions": False,
        }
        if run_config is not None:
            evaluate_kwargs["run_config"] = run_config

        result = evaluate(
            **evaluate_kwargs,
        )
    except Exception as exc:
        reason = f"RAGAS evaluation skipped after evaluator error: {exc}"
        rows = [
            {"case_id": case["case_id"], "trace_id": case["trace_id"], "scores": _empty_scores(metric_names, reason)}
            for case in cases
        ]
        return rows, reason

    if hasattr(result, "to_pandas"):
        frame = result.to_pandas()
        return [
            {
                "case_id": case["case_id"],
                "trace_id": case["trace_id"],
                "scores": {name: {"score": _safe_score(frame.iloc[index].get(name))} for name in metric_names},
            }
            for index, case in enumerate(cases)
        ], None

    aggregate = dict(result)
    return [
        {
            "case_id": case["case_id"],
            "trace_id": case["trace_id"],
            "scores": {name: {"score": _safe_score(aggregate.get(name))} for name in metric_names},
        }
        for case in cases
    ], None


def _apply_thresholds(rows: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    thresholds = _thresholds(config)
    for row in rows:
        failed = []
        for metric_name, metric_result in row.get("scores", {}).items():
            score = _safe_score(metric_result.get("score"))
            threshold = thresholds.get(metric_name)
            metric_result["threshold"] = threshold
            if score is None:
                metric_result.setdefault("passed", None)
                metric_result.setdefault("skipped", True)
                continue
            metric_result["skipped"] = False
            metric_result["passed"] = threshold is None or score >= threshold
            if threshold is not None and score < threshold:
                failed.append(metric_name)

        metrics = list(row.get("scores", {}).values())
        row["evaluated"] = any(metric.get("score") is not None for metric in metrics)
        row["fully_evaluated"] = bool(metrics) and all(
            metric.get("score") is not None for metric in metrics
        )
        row["skipped"] = not row["fully_evaluated"]
        row["failed_thresholds"] = failed
        row["passed"] = (
            True
            if row["fully_evaluated"] and not failed and all(metric.get("passed") is not False for metric in metrics)
            else None
        )
        row["notes"] = (
            "Use this offline result for retrieval gate threshold calibration only; "
            "RAGAS does not trigger retry, fallback, or query rewrite."
        )
    return rows


def evaluate_ragas_offline(cases: list[dict[str, Any]], config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate traces/golden cases with RAGAS, enforcing offline-only mode."""
    config = config or load_eval_config()
    ragas_config = get_config_value(config, "eval.ragas", {})
    run_mode = ragas_config.get("run_mode", "offline_only")
    if run_mode != "offline_only":
        raise RagasOfflineOnlyError("RAGAS run_mode must be offline_only.")

    normalized = [_normalize_case(case, index) for index, case in enumerate(cases)]
    invalid_cases = []
    valid_cases = []
    for case in normalized:
        missing_fields = _validate_case(case)
        if missing_fields:
            invalid_cases.append(
                {
                    "case_id": case["case_id"],
                    "trace_id": case["trace_id"],
                    "missing_fields": missing_fields,
                    "notes": "Case was not sent to RAGAS because required evaluation inputs are missing.",
                }
            )
        else:
            valid_cases.append(case)

    metric_names = _metric_names_for_cases(valid_cases)

    if not ragas_config.get("enabled", False):
        rows = [
            {"case_id": case["case_id"], "trace_id": case["trace_id"], "scores": _empty_scores(metric_names, "eval.ragas.enabled is false.")}
            for case in valid_cases
        ]
        setup_note = "RAGAS disabled by config."
    elif not valid_cases:
        rows = []
        setup_note = "No valid RAGAS cases to evaluate."
    else:
        rows, setup_note = _run_ragas(valid_cases, config)

    rows = _apply_thresholds(rows, config)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_mode": run_mode,
        "metrics": metric_names,
        "case_count": len(normalized),
        "valid_case_count": len(valid_cases),
        "invalid_case_count": len(invalid_cases),
        "evaluated_count": sum(1 for row in rows if row["evaluated"]),
        "skipped_count": sum(1 for row in rows if row["skipped"]),
        "passed": (
            all(row["passed"] for row in rows)
            if rows and all(row["fully_evaluated"] for row in rows)
            else None
        ),
        "setup_note": setup_note,
        "invalid_cases": invalid_cases,
        "results": rows,
        "calibration_notes": [
            "Compare failed RAGAS metrics with runtime retrieval gate signals.",
            "Tune retrieval gate thresholds empirically; do not invoke Retry Retrieve from this report.",
        ],
    }


def write_ragas_report(report: dict[str, Any], output_path: str | Path | None = None) -> Path:
    output = Path(output_path) if output_path else DEFAULT_REPORT_DIR / (
        "ragas_report_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return output
