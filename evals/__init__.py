"""Evaluation foundation contracts for the Streamlit runtime."""

from .config import load_eval_config
from .auto_retrieve import retrieve_with_gate_retry, retry_retrieve
from .retrieval_gate import evaluate_retrieval_gate
from .summary_eval import evaluate_summary, should_retry_summary_eval
from .trace import PipelineTrace, build_trace, contexts_from_retrieval_results

__all__ = [
    "PipelineTrace",
    "build_trace",
    "contexts_from_retrieval_results",
    "evaluate_retrieval_gate",
    "evaluate_summary",
    "load_eval_config",
    "retrieve_with_gate_retry",
    "retry_retrieve",
    "should_retry_summary_eval",
]
