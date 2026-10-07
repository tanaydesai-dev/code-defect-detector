"""Load and inspect the CodeXGLUE defect-detection dataset."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from statistics import mean, median
from typing import Any

DEFAULT_DATASET = "google/code_x_glue_cc_defect_detection"
EXPECTED_COLUMNS = {"id", "func", "target", "project", "commit_id"}


def load_codexglue_dataset(
    dataset_name: str = DEFAULT_DATASET,
    revision: str = "main",
) -> Any:
    """Load the official CodeXGLUE splits from the Hugging Face Hub."""
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise RuntimeError("Install the project dependencies before loading data") from exc

    return load_dataset(dataset_name, revision=revision)


def normalize_code(source: str) -> str:
    """Create a conservative whitespace-normalized form for duplicate checks."""
    return re.sub(r"\s+", " ", source).strip()


def _digest(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _distribution(values: Sequence[int]) -> dict[str, float | int | None]:
    if not values:
        return {"min": None, "median": None, "mean": None, "max": None}
    return {
        "min": min(values),
        "median": median(values),
        "mean": mean(values),
        "max": max(values),
    }


def inspect_splits(
    splits: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    tokenizer: Any | None = None,
    max_length: int = 512,
    limit: int | None = None,
) -> dict[str, Any]:
    """Compute split statistics and exact/normalized cross-split duplicates."""
    report: dict[str, Any] = {"splits": {}}
    exact_locations: dict[str, set[str]] = defaultdict(set)
    normalized_locations: dict[str, set[str]] = defaultdict(set)

    for split_name, split in splits.items():
        rows = list(split) if limit is None else list(itertools.islice(split, limit))
        label_counts: Counter[int] = Counter()
        project_counts: Counter[str] = Counter()
        char_lengths: list[int] = []
        line_lengths: list[int] = []
        token_lengths: list[int] = []
        invalid_rows = 0

        for row in rows:
            source = row.get("func")
            label = row.get("target")
            if not isinstance(source, str) or label is None:
                invalid_rows += 1
                continue

            label_counts[int(label)] += 1
            if row.get("project") is not None:
                project_counts[str(row["project"])] += 1
            char_lengths.append(len(source))
            line_lengths.append(source.count("\n") + 1)
            exact_locations[_digest(source)].add(split_name)
            normalized_locations[_digest(normalize_code(source))].add(split_name)

            if tokenizer is not None:
                encoded = tokenizer(source, add_special_tokens=True, truncation=False)
                token_lengths.append(len(encoded["input_ids"]))

        split_report: dict[str, Any] = {
            "rows_inspected": len(rows),
            "invalid_rows": invalid_rows,
            "label_counts": dict(sorted(label_counts.items())),
            "project_counts": dict(sorted(project_counts.items())),
            "character_length": _distribution(char_lengths),
            "line_length": _distribution(line_lengths),
        }
        if tokenizer is not None:
            split_report["token_length"] = _distribution(token_lengths)
            split_report["examples_over_max_length"] = sum(
                length > max_length for length in token_lengths
            )
        report["splits"][split_name] = split_report

    report["cross_split_duplicates"] = {
        "exact_hashes": sum(len(names) > 1 for names in exact_locations.values()),
        "whitespace_normalized_hashes": sum(
            len(names) > 1 for names in normalized_locations.values()
        ),
    }
    return report


def validate_columns(splits: Mapping[str, Any]) -> None:
    """Fail clearly when the upstream dataset schema changes."""
    for split_name, split in splits.items():
        columns = set(getattr(split, "column_names", []))
        missing = EXPECTED_COLUMNS - columns
        if missing:
            raise ValueError(f"Split {split_name!r} is missing columns: {sorted(missing)}")


def sample_examples(
    splits: Mapping[str, Any], count: int, seed: int
) -> dict[str, list[dict[str, Any]]]:
    """Sample positive and negative examples without modifying dataset order."""
    rng = random.Random(seed)
    result: dict[str, list[dict[str, Any]]] = {}
    for split_name, split in splits.items():
        by_label: dict[int, list[int]] = defaultdict(list)
        for index, label in enumerate(split["target"]):
            by_label[int(label)].append(index)
        chosen: list[dict[str, Any]] = []
        for label in sorted(by_label):
            indices = rng.sample(by_label[label], min(count, len(by_label[label])))
            for index in indices:
                row = dict(split[index])
                chosen.append(
                    {
                        "id": row.get("id"),
                        "label": int(row["target"]),
                        "project": row.get("project"),
                        "source": row["func"],
                    }
                )
        result[split_name] = chosen
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--revision", default="main")
    parser.add_argument("--tokenizer", help="Tokenizer ID for token-length statistics")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--limit", type=int, help="Inspect at most this many rows per split")
    parser.add_argument("--examples", type=int, default=0, help="Samples per label and split")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    """CLI entry point for reproducible dataset inspection."""
    args = _parse_args()
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if args.examples < 0:
        raise SystemExit("--examples cannot be negative")

    dataset = load_codexglue_dataset(args.dataset, args.revision)
    validate_columns(dataset)

    tokenizer = None
    if args.tokenizer:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, use_fast=True)

    report = inspect_splits(
        dataset,
        tokenizer=tokenizer,
        max_length=args.max_length,
        limit=args.limit,
    )
    report["dataset"] = args.dataset
    report["requested_revision"] = args.revision
    report["fingerprints"] = {
        name: getattr(split, "_fingerprint", None) for name, split in dataset.items()
    }
    if args.tokenizer:
        report["tokenizer"] = args.tokenizer
        report["max_length"] = args.max_length
    if args.examples:
        report["examples"] = sample_examples(dataset, args.examples, args.seed)

    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
