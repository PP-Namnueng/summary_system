import pytest
import subprocess
import sys
import types

from evals.ragas_eval import (
    RagasOfflineOnlyError,
    _apply_thresholds,
    _build_langchain_judge,
    _run_ragas,
    evaluate_ragas_offline,
    load_ragas_cases,
)


def _case():
    return {
        "case_id": "case-1",
        "trace": {
            "trace_id": "trace-1",
            "query": "What is a fixture?",
            "contexts": [{"text": "A pytest fixture is reusable setup for tests."}],
            "summary": "A fixture provides reusable test setup.",
        },
        "ground_truth": "A fixture is reusable setup for tests.",
    }


def test_ragas_offline_report_skips_when_disabled():
    report = evaluate_ragas_offline(
        [_case()],
        {
            "eval": {
                "ragas": {
                    "enabled": False,
                    "run_mode": "offline_only",
                    "thresholds": {
                        "faithfulness": 0.8,
                        "answer_relevancy": 0.75,
                        "context_precision": 0.7,
                        "context_recall": 0.7,
                    },
                }
            }
        },
    )

    assert report["case_count"] == 1
    assert report["evaluated_count"] == 0
    assert report["skipped_count"] == 1
    assert report["passed"] is None
    assert report["metrics"] == [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ]
    assert report["results"][0]["trace_id"] == "trace-1"
    assert report["results"][0]["passed"] is None
    assert report["results"][0]["evaluated"] is False
    assert report["results"][0]["fully_evaluated"] is False
    assert report["results"][0]["skipped"] is True
    assert report["results"][0]["failed_thresholds"] == []
    assert report["results"][0]["scores"]["faithfulness"]["skipped"] is True


def test_ragas_enforces_offline_only():
    with pytest.raises(RagasOfflineOnlyError):
        evaluate_ragas_offline(
            [_case()],
            {"eval": {"ragas": {"enabled": True, "run_mode": "runtime"}}},
        )


def test_load_ragas_cases_reads_jsonl(tmp_path):
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text(
        '{"case_id":"case-1","query":"Q","contexts":["C"],"summary":"A"}\n',
        encoding="utf-8",
    )

    cases = load_ragas_cases(dataset)

    assert cases[0]["case_id"] == "case-1"
    assert cases[0]["question"] == "Q"
    assert cases[0]["contexts"] == ["C"]


def test_context_recall_requires_ground_truth_for_every_case():
    report = evaluate_ragas_offline(
        [
            _case(),
            {
                "case_id": "case-2",
                "trace": {
                    "trace_id": "trace-2",
                    "query": "What is pytest?",
                    "contexts": [{"text": "Pytest is a testing framework."}],
                    "summary": "Pytest is a testing framework.",
                },
            },
        ],
        {"eval": {"ragas": {"enabled": False, "run_mode": "offline_only"}}},
    )

    assert "context_recall" not in report["metrics"]


def test_gemini_judge_requires_external_opt_in(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    llm, embeddings, error = _build_langchain_judge(
        {
            "llm": {"gemini": {"api_key_env": "GEMINI_API_KEY"}},
            "eval": {
                "ragas": {
                    "judge": {
                        "provider": "gemini",
                        "fallback_provider": "none",
                        "allow_external": False,
                    }
                }
            },
        }
    )

    assert llm is None
    assert embeddings is None
    assert "allow_external is false" in error


def test_openrouter_judge_uses_chat_openai_and_ollama_embeddings(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    openai_module = types.ModuleType("langchain_openai")

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    openai_module.ChatOpenAI = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", openai_module)

    ollama_module = types.ModuleType("langchain_ollama")

    class FakeOllamaEmbeddings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    ollama_module.OllamaEmbeddings = FakeOllamaEmbeddings
    monkeypatch.setitem(sys.modules, "langchain_ollama", ollama_module)

    llm, embeddings, error = _build_langchain_judge(
        {
            "llm": {
                "generator": {"base_url": "http://localhost:11434"},
                "openrouter": {
                    "api_key_env": "OPENROUTER_API_KEY",
                    "base_url": "https://openrouter.ai/api/v1",
                    "model": "openai/gpt-4.1-nano",
                },
            },
            "eval": {
                "ragas": {
                    "judge": {
                        "provider": "openrouter",
                        "fallback_provider": "ollama",
                        "allow_external": True,
                        "embeddings_provider": "ollama",
                        "ollama_embedding_model": "nomic-embed-text",
                    }
                }
            },
        }
    )

    assert error is None
    assert llm.kwargs["model"] == "openai/gpt-4.1-nano"
    assert llm.kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert embeddings.kwargs["model"] == "nomic-embed-text"


def test_invalid_cases_are_reported_before_ragas():
    report = evaluate_ragas_offline(
        [
            {
                "case_id": "bad-case",
                "query": "",
                "contexts": [],
                "summary": "",
            }
        ],
        {"eval": {"ragas": {"enabled": True, "run_mode": "offline_only"}}},
    )

    assert report["case_count"] == 1
    assert report["valid_case_count"] == 0
    assert report["invalid_case_count"] == 1
    assert report["evaluated_count"] == 0
    assert report["passed"] is None
    assert report["invalid_cases"][0]["missing_fields"] == [
        "question",
        "answer",
        "contexts",
    ]


def test_run_ragas_uses_installed_evaluator_path(monkeypatch):
    ragas_module = types.ModuleType("ragas")

    def fake_evaluate(dataset, metrics, llm, embeddings, raise_exceptions):
        assert len(dataset.rows) == 1
        assert [metric.name for metric in metrics] == [
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
        ]
        assert raise_exceptions is False
        return {
            "faithfulness": 0.91,
            "answer_relevancy": 0.92,
            "context_precision": 0.93,
            "context_recall": 0.94,
        }

    ragas_module.evaluate = fake_evaluate
    ragas_module.metrics = types.SimpleNamespace(
        faithfulness=types.SimpleNamespace(name="faithfulness"),
        answer_relevancy=types.SimpleNamespace(name="answer_relevancy"),
        context_precision=types.SimpleNamespace(name="context_precision"),
        context_recall=types.SimpleNamespace(name="context_recall"),
    )
    monkeypatch.setitem(sys.modules, "ragas", ragas_module)

    datasets_module = types.ModuleType("datasets")

    class FakeDataset:
        def __init__(self, rows):
            self.rows = rows

        @classmethod
        def from_list(cls, rows):
            return cls(rows)

    datasets_module.Dataset = FakeDataset
    monkeypatch.setitem(sys.modules, "datasets", datasets_module)

    ollama_module = types.ModuleType("langchain_ollama")

    class FakeChatOllama:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeOllamaEmbeddings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    ollama_module.ChatOllama = FakeChatOllama
    ollama_module.OllamaEmbeddings = FakeOllamaEmbeddings
    monkeypatch.setitem(sys.modules, "langchain_ollama", ollama_module)

    rows, setup_note = _run_ragas(
        [
            {
                "case_id": "case-1",
                "trace_id": "trace-1",
                "question": "Q",
                "answer": "A",
                "contexts": ["C"],
                "ground_truth": "GT",
            }
        ],
        {
            "llm": {"generator": {"base_url": "http://localhost:11434"}},
            "eval": {
                "ragas": {
                    "judge": {
                        "provider": "ollama",
                        "fallback_provider": "ollama",
                        "ollama_model": "judge-model",
                    }
                }
            },
        },
    )

    assert setup_note is None
    assert rows[0]["scores"]["faithfulness"]["score"] == 0.91
    assert rows[0]["scores"]["context_recall"]["score"] == 0.94


def test_run_ragas_passes_run_config_when_configured(monkeypatch):
    ragas_module = types.ModuleType("ragas")
    observed = {}

    def fake_evaluate(**kwargs):
        observed.update(kwargs)
        return {
            "faithfulness": 0.91,
            "answer_relevancy": 0.92,
            "context_precision": 0.93,
            "context_recall": 0.94,
        }

    ragas_module.evaluate = fake_evaluate
    ragas_module.metrics = types.SimpleNamespace(
        faithfulness=types.SimpleNamespace(name="faithfulness"),
        answer_relevancy=types.SimpleNamespace(name="answer_relevancy"),
        context_precision=types.SimpleNamespace(name="context_precision"),
        context_recall=types.SimpleNamespace(name="context_recall"),
    )
    run_config_module = types.ModuleType("ragas.run_config")

    class FakeRunConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    run_config_module.RunConfig = FakeRunConfig
    monkeypatch.setitem(sys.modules, "ragas", ragas_module)
    monkeypatch.setitem(sys.modules, "ragas.run_config", run_config_module)

    datasets_module = types.ModuleType("datasets")

    class FakeDataset:
        @classmethod
        def from_list(cls, rows):
            return rows

    datasets_module.Dataset = FakeDataset
    monkeypatch.setitem(sys.modules, "datasets", datasets_module)

    ollama_module = types.ModuleType("langchain_ollama")

    class FakeChatOllama:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeOllamaEmbeddings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    ollama_module.ChatOllama = FakeChatOllama
    ollama_module.OllamaEmbeddings = FakeOllamaEmbeddings
    monkeypatch.setitem(sys.modules, "langchain_ollama", ollama_module)

    _run_ragas(
        [
            {
                "case_id": "case-1",
                "trace_id": "trace-1",
                "question": "Q",
                "answer": "A",
                "contexts": ["C"],
                "ground_truth": "GT",
            }
        ],
        {
            "llm": {"generator": {"base_url": "http://localhost:11434"}},
            "eval": {
                "ragas": {
                    "judge": {
                        "provider": "ollama",
                        "fallback_provider": "ollama",
                        "ollama_model": "judge-model",
                        "max_workers": 2,
                        "max_retries": 1,
                        "timeout_seconds": 180,
                        "max_wait_seconds": 30,
                    }
                }
            },
        },
    )

    assert observed["run_config"].kwargs == {
        "max_workers": 2,
        "max_retries": 1,
        "timeout": 180,
        "max_wait": 30,
    }


def test_cli_require_evaluated_fails_when_everything_skips(tmp_path):
    report_path = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_ragas_eval.py",
            "--output",
            str(report_path),
            "--require-evaluated",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 3
    assert report_path.exists()


def test_partial_metric_scores_do_not_pass_case():
    rows = _apply_thresholds(
        [
            {
                "case_id": "case-1",
                "trace_id": "trace-1",
                "scores": {
                    "faithfulness": {"score": 0.9},
                    "answer_relevancy": {"score": None},
                },
            }
        ],
        {"eval": {"ragas": {"thresholds": {"faithfulness": 0.8, "answer_relevancy": 0.75}}}},
    )

    assert rows[0]["evaluated"] is True
    assert rows[0]["fully_evaluated"] is False
    assert rows[0]["skipped"] is True
    assert rows[0]["passed"] is None
