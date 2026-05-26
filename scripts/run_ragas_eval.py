"""Manual offline RAGAS runner for Streamlit pipeline traces and golden cases."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evals.config import load_eval_config
from evals.ragas_eval import DEFAULT_GOLDEN_DATASET, evaluate_ragas_offline, load_ragas_cases, write_ragas_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline RAGAS evaluation over traces or golden cases.")
    parser.add_argument("--input", default=str(DEFAULT_GOLDEN_DATASET), help="JSON/JSONL trace or golden dataset file.")
    parser.add_argument("--config", help="Optional YAML config path. Defaults to config.local.yaml merged with defaults.")
    parser.add_argument("--output", help="Optional report JSON path. Defaults to reports/ragas_report_*.json.")
    parser.add_argument("--require-evaluated", action="store_true", help="Exit non-zero when no cases were evaluated.")
    parser.add_argument("--fail-on-skip", action="store_true", help="Exit non-zero when any valid case or metric was skipped.")
    parser.add_argument("--fail-on-threshold", action="store_true", help="Exit non-zero when evaluated scores fail configured thresholds.")
    args = parser.parse_args()

    config = load_eval_config(args.config)
    cases = load_ragas_cases(args.input)
    report = evaluate_ragas_offline(cases, config)
    output = write_ragas_report(report, args.output)

    print(
        json.dumps(
            {
                "output": str(output),
                "case_count": report["case_count"],
                "valid_case_count": report["valid_case_count"],
                "invalid_case_count": report["invalid_case_count"],
                "evaluated_count": report["evaluated_count"],
                "skipped_count": report["skipped_count"],
                "passed": report["passed"],
                "setup_note": report.get("setup_note"),
            },
            indent=2,
        )
    )
    if report["invalid_case_count"]:
        return 2
    if args.require_evaluated and report["evaluated_count"] == 0:
        return 3
    if args.fail_on_skip and report["skipped_count"] > 0:
        return 4
    if args.fail_on_threshold and report["passed"] is False:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
