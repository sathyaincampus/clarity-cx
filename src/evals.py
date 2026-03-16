"""
Clarity CX — Inline Evaluation Pipeline

Runs LLM-as-judge evaluations automatically after each call analysis
and logs results back to Phoenix as span annotations.

Uses Gemini Flash as the judge model (free tier).

Evaluates 5 metrics:
- Relevance:        Does the summary address what happened in the call?
- Hallucination:    Is the summary grounded in the transcript (no fabrication)?
- QA Quality:       Is the quality score accurate and helpful?
- Toxicity:         Is the output free of harmful content?
- Summarization:    Quality of the call summary

Results appear in Phoenix under "Annotations" for each trace span.
"""

from __future__ import annotations

import os
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)


def _get_eval_model():
    """Get the LLM judge model — prefers Gemini (free), falls back to OpenAI."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    google_key = os.getenv("GOOGLE_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if google_key:
        try:
            from phoenix.evals import GoogleGenAIModel
            return GoogleGenAIModel(
                model="gemini-2.0-flash",
                api_key=google_key,
            )
        except Exception:
            pass

    if openai_key:
        try:
            from phoenix.evals import OpenAIModel
            return OpenAIModel(model="gpt-4o-mini", api_key=openai_key)
        except Exception:
            pass

    return None


def _get_phoenix_client():
    """Get Phoenix client with correct base_url for Phoenix 13.x."""
    try:
        from phoenix.client import Client as PhoenixClient
        return PhoenixClient(base_url="http://localhost:6006")
    except Exception:
        return None


def run_evals_on_response(
    user_input: str,
    response: str,
    span_id: Optional[str] = None,
) -> dict:
    """
    Run Phoenix LLM-as-judge evaluations on a single pipeline output.

    Uses Gemini Flash as judge (free tier). Falls back to GPT-4o-mini.
    Evaluates: relevance, hallucination, QA quality, toxicity, summarization.

    If span_id is provided, logs annotations to Phoenix. Otherwise, finds
    the most recent span automatically.

    Returns dict of {metric_name: {score, label, explanation}}.
    """
    if os.getenv("PHOENIX_ENABLED", "true").lower() != "true":
        return {}

    eval_model = _get_eval_model()
    if not eval_model:
        logger.debug("No eval model available (set GOOGLE_API_KEY or OPENAI_API_KEY)")
        return {}

    try:
        from phoenix.evals import (
            HallucinationEvaluator,
            QAEvaluator,
            RelevanceEvaluator,
            ToxicityEvaluator,
        )
    except ImportError:
        return {}

    # If no span_id, try to find the latest
    if not span_id:
        span_id = _find_latest_span_id()

    eval_results = {}

    # Build the record dict that evaluators expect
    record = {
        "input": user_input,
        "output": response,
        "reference": user_input,  # transcript serves as ground truth
    }

    # ── Run built-in evaluators ──────────────────────────────────
    evaluators = {
        "Relevance": RelevanceEvaluator,
        "QA Quality": QAEvaluator,
        "Toxicity": ToxicityEvaluator,
        "Hallucination": HallucinationEvaluator,
    }

    # Optional: Summarization
    try:
        from phoenix.evals import SummarizationEvaluator
        evaluators["Summarization"] = SummarizationEvaluator
    except (ImportError, Exception):
        pass

    for name, evaluator_class in evaluators.items():
        try:
            evaluator = evaluator_class(eval_model)
            label, score, explanation = evaluator.evaluate(
                record, provide_explanation=True
            )
            eval_results[name] = {
                "score": score if score is not None else 0,
                "label": label or "",
                "explanation": explanation or "",
            }
        except Exception as e:
            logger.debug(f"{name} eval failed: {e}")

    # ── Log to Phoenix ───────────────────────────────────────────
    if span_id and eval_results:
        _log_evals_to_phoenix(eval_results, span_id)
        logger.info(f"✅ Logged {len(eval_results)} evals to span {span_id[:12]}...")

    return eval_results


def run_evals_async(user_input: str, response: str, span_id: Optional[str] = None):
    """
    Run evaluations in a background thread so the UI doesn't block.
    Returns immediately — results are logged to Phoenix asynchronously.
    """
    thread = threading.Thread(
        target=run_evals_on_response,
        args=(user_input, response, span_id),
        daemon=True,
    )
    thread.start()
    return thread


def _find_latest_span_id() -> Optional[str]:
    """Find the most recent span ID from Phoenix to attach evaluations to."""
    try:
        import time
        client = _get_phoenix_client()
        if not client:
            return None

        # Retry — span may not be flushed yet
        for attempt in range(3):
            time.sleep(2 + attempt * 2)  # 2s, 4s, 6s
            try:
                spans_df = client.spans.get_spans_dataframe(
                    project_name="clarity-cx",
                )
                if spans_df is not None and not spans_df.empty:
                    span_id = str(spans_df.index[0])
                    logger.info(f"Found span {span_id[:12]}... on attempt {attempt + 1}")
                    return span_id
            except Exception:
                continue
    except Exception as e:
        logger.warning(f"Could not find latest span: {e}")

    return None


def _log_evals_to_phoenix(eval_results: dict, span_id: str):
    """Log evaluation results to Phoenix as span annotations (Phoenix 13.x API)."""
    if not eval_results or not span_id:
        return

    try:
        client = _get_phoenix_client()
        if not client:
            return

        for eval_name, result in eval_results.items():
            try:
                label = str(result.get("label", "")) if result.get("label") is not None else None
                score = float(result.get("score")) if result.get("score") is not None else None
                explanation = str(result.get("explanation", "")) if result.get("explanation") is not None else None

                client.spans.add_span_annotation(
                    span_id=span_id,
                    annotation_name=eval_name,
                    annotator_kind="LLM",
                    label=label,
                    score=score,
                    explanation=explanation,
                )
            except Exception as e:
                logger.debug(f"Failed to log {eval_name} to Phoenix: {e}")

    except Exception as e:
        logger.debug(f"Failed to log evals to Phoenix: {e}")
