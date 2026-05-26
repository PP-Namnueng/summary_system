# Offline RAGAS Evaluation

RAGAS is wired as a manual/offline evaluator for Streamlit pipeline traces and
golden dataset cases. It is not part of the normal request path and must not be
used to trigger Retry Retrieve, fallback, blocking, or query rewrite.

Run the default golden dataset:

```powershell
python scripts\run_ragas_eval.py
```

Use a trace or dataset file:

```powershell
python scripts\run_ragas_eval.py --input data\golden\ragas_cases.jsonl
```

For CI or regression checks, use stricter exit behavior:

```powershell
python scripts\run_ragas_eval.py --require-evaluated --fail-on-skip --fail-on-threshold
```

Reports include metric scores, thresholds, pass/fail, failed thresholds,
case/trace IDs, invalid cases, skipped cases, and calibration notes.

## External Judge Privacy

Gemini is supported as an optional judge, but it sends trace questions,
contexts, answers, and references to an external API. The default config blocks
external judging:

```yaml
eval:
  ragas:
    judge:
      provider: gemini
      allow_external: false
```

Set `allow_external: true` only for traces and datasets that are safe to send to
Gemini. If this remains false, the runner falls back to the configured local
provider when possible or skips LLM-based metrics with an explicit report note.

## Required Case Fields

Each case must provide:

- `query` or `question`
- `summary` or `answer`
- non-empty `contexts` or `retrieved_contexts`

`context_recall` is included only when every valid case has `ground_truth` or
`reference`.
