"""
Clarity CX — Evaluation Dataset Loader

Loads large-scale call center transcript datasets for pipeline evaluation.

Supported Datasets:
─────────────────────────────────────────────────────────────────
| Dataset        | Size     | Source          | Type                |
|----------------|----------|-----------------|---------------------|
| DialogSum      | 13,460   | HuggingFace     | Dialogue + summaries|
| TWEETSUMM      | 6,500    | HuggingFace     | Customer service    |
| CallCenterEN   | 91,706   | HuggingFace     | Real call center    |
─────────────────────────────────────────────────────────────────

Usage:
    python -m src.eval.dataset_loader --dataset dialogsum --limit 100
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Dataset configs
DATASETS = {
    "dialogsum": {
        "huggingface_id": "knkarthick/dialogsum",
        "description": "13,460 dialogues with human-annotated summaries",
        "split": "test",  # Use test split for evaluation
        "transcript_field": "dialogue",
        "summary_field": "summary",
        "id_field": "id",
    },
    "tweetsumm": {
        "huggingface_id": "empirical-org/tweetsumm",
        "description": "6,500 customer service Twitter conversations with summaries",
        "split": "test",
        "transcript_field": "dialogue",
        "summary_field": "summary",
        "id_field": "id",
    },
    "samsum": {
        "huggingface_id": "samsum",
        "description": "16,369 chat dialogues with human summaries (Samsung)",
        "split": "test",
        "transcript_field": "dialogue",
        "summary_field": "summary",
        "id_field": "id",
    },
}


def load_dataset_from_huggingface(
    dataset_name: str = "dialogsum",
    limit: Optional[int] = None,
    cache_dir: Optional[str] = None,
) -> list[dict]:
    """
    Load a dataset from HuggingFace for evaluation.

    Args:
        dataset_name: One of 'dialogsum', 'tweetsumm', 'samsum'
        limit: Max number of samples to load
        cache_dir: Directory to cache downloaded datasets

    Returns:
        List of dicts with 'id', 'transcript', 'reference_summary' keys
    """
    if dataset_name not in DATASETS:
        raise ValueError(f"Unknown dataset: {dataset_name}. Available: {list(DATASETS.keys())}")

    config = DATASETS[dataset_name]

    try:
        from datasets import load_dataset

        logger.info(f"Loading {dataset_name} from HuggingFace ({config['description']})...")

        ds = load_dataset(
            config["huggingface_id"],
            split=config["split"],
            cache_dir=cache_dir,
        )

        samples = []
        for i, item in enumerate(ds):
            if limit and i >= limit:
                break

            samples.append({
                "id": str(item.get(config["id_field"], f"{dataset_name}_{i}")),
                "transcript": item[config["transcript_field"]],
                "reference_summary": item.get(config["summary_field"], ""),
                "dataset": dataset_name,
            })

        logger.info(f"Loaded {len(samples)} samples from {dataset_name}")
        return samples

    except ImportError:
        logger.error("Install 'datasets' package: pip install datasets")
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise


def load_local_samples() -> list[dict]:
    """Load the built-in sample transcripts."""
    samples_path = Path(__file__).parent.parent.parent / "data" / "sample_transcripts" / "samples.json"
    if not samples_path.exists():
        return []

    with open(samples_path) as f:
        raw_samples = json.load(f)

    return [
        {
            "id": s["call_id"],
            "transcript": "\n".join(
                f"[{seg['timestamp']}] {seg['speaker']}: {seg['text']}"
                for seg in s["transcript"]
            ),
            "reference_summary": "",
            "expected_score": s.get("expected_score"),
            "dataset": "local_samples",
        }
        for s in raw_samples
    ]


def save_dataset_cache(samples: list[dict], output_path: str):
    """Save downloaded dataset to local JSON for offline use."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(samples, f, indent=2)
    logger.info(f"Cached {len(samples)} samples to {output_path}")


def load_dataset_cache(cache_path: str) -> list[dict]:
    """Load previously cached dataset."""
    with open(cache_path) as f:
        return json.load(f)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download evaluation datasets")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()), default="dialogsum")
    parser.add_argument("--limit", type=int, default=100, help="Max samples to download")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    samples = load_dataset_from_huggingface(args.dataset, limit=args.limit)

    output = args.output or f"data/eval_datasets/{args.dataset}_{args.limit}.json"
    save_dataset_cache(samples, output)

    print(f"\n✅ Downloaded {len(samples)} samples from {args.dataset}")
    print(f"📁 Saved to: {output}")
    print(f"\nSample transcript preview:")
    print(f"  {samples[0]['transcript'][:200]}...")
