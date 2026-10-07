# StructRoute

StructRoute tests whether explicit token-level C syntax improves routing in a
mixture of lightweight adapter experts for defect detection. The first
milestone establishes a reproducible CodeXGLUE data pipeline and a frozen
CodeBERT classifier baseline. Expert routing is deliberately out of scope
until the baseline and syntax-alignment gates pass.

## Setup

Python 3.10 or 3.11 is recommended. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

The dataset is governed by the Computational Use of Data Agreement (C-UDA).
Review its terms on the Hugging Face dataset page before downloading it.

## Inspect the dataset

The first command downloads the current Hugging Face Parquet snapshot into the
normal Hugging Face cache. Raw data is not written into Git:

```bash
structroute-inspect-data --output reports/results/dataset_stats.json
```

To add CodeBERT token-length and truncation statistics (this also downloads the
tokenizer):

```bash
structroute-inspect-data \
  --tokenizer microsoft/codebert-base \
  --max-length 512 \
  --output reports/results/dataset_stats_with_tokens.json
```

For a quick smoke test, limit work per split:

```bash
structroute-inspect-data --limit 100 --examples 1
```

Use `--revision <commit>` to pin a known Hugging Face dataset revision. Every
report records the requested revision and the loaded split fingerprints.

Run local tests and linting with:

```bash
pytest
ruff check .
```

## Current milestone

Milestone 1 is in progress. Dataset inspection is implemented; preprocessing,
the frozen-CodeBERT classifier, and its small-set overfit check remain.

