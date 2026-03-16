"""
Run Clarity CX evaluations — evaluates pipeline traces in Phoenix.

Usage (3 terminals):
    Terminal 1: python -c "import phoenix as px; px.launch_app(); input('Phoenix running...')"
    Terminal 2: PHOENIX_ENABLED=true streamlit run src/ui/app.py
               → Analyze at least one call in the UI
    Terminal 3: python scripts/run_evals.py
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    google_key = os.getenv("GOOGLE_API_KEY", "")
    if not google_key:
        logger.error("❌ GOOGLE_API_KEY not set. Add it to .env")
        sys.exit(1)

    # ── Connect to Phoenix ───────────────────────────────────────
    try:
        from phoenix.client import Client as PhoenixClient
        client = PhoenixClient(base_url="http://localhost:6006")
        logger.info("✅ Connected to Phoenix at http://localhost:6006")
    except Exception as e:
        logger.error(f"❌ Cannot connect to Phoenix: {e}")
        sys.exit(1)

    # ── Fetch spans ──────────────────────────────────────────────
    spans_df = None
    for pname in ["clarity-cx", "default"]:
        try:
            df = client.spans.get_spans_dataframe(project_name=pname)
            if df is not None and not df.empty:
                spans_df = df
                logger.info(f"📊 Found {len(df)} spans in project '{pname}'")
                break
        except Exception as e:
            logger.info(f"   Project '{pname}': {e}")

    if spans_df is None or spans_df.empty:
        logger.error("❌ No spans found. Analyze a call first.")
        sys.exit(1)

    # ── Map columns for evaluators ───────────────────────────────
    col_map = {}
    if "attributes.input.value" in spans_df.columns:
        col_map["attributes.input.value"] = "input"
    if "attributes.output.value" in spans_df.columns:
        col_map["attributes.output.value"] = "output"
    if col_map:
        spans_df = spans_df.rename(columns=col_map)

    if "reference" not in spans_df.columns and "input" in spans_df.columns:
        spans_df["reference"] = spans_df["input"]

    for col in ["input", "output", "reference"]:
        if col in spans_df.columns:
            spans_df[col] = spans_df[col].fillna("")

    # ── Set up eval model ────────────────────────────────────────
    try:
        from phoenix.evals import GoogleGenAIModel
        eval_model = GoogleGenAIModel(model="gemini-2.0-flash", api_key=google_key)
        logger.info("✅ Using Gemini 2.0 Flash as judge model")
    except Exception as e:
        logger.error(f"❌ Cannot create eval model: {e}")
        sys.exit(1)

    # ── Import evaluators ────────────────────────────────────────
    from phoenix.evals import (
        HallucinationEvaluator,
        QAEvaluator,
        RelevanceEvaluator,
        ToxicityEvaluator,
        run_evals,
    )

    evaluator_configs = [
        ("Relevance", RelevanceEvaluator(eval_model)),
        ("QA Quality", QAEvaluator(eval_model)),
        ("Toxicity", ToxicityEvaluator(eval_model)),
        ("Hallucination", HallucinationEvaluator(eval_model)),
    ]

    try:
        from phoenix.evals import SummarizationEvaluator
        evaluator_configs.append(("Summarization", SummarizationEvaluator(eval_model)))
    except (ImportError, Exception):
        pass

    logger.info(f"\n🧪 Running {len(evaluator_configs)} evaluators on {len(spans_df)} spans...\n")

    # ── Run each evaluator and log results one-by-one ────────────
    success_count = 0
    for eval_name, evaluator in evaluator_configs:
        try:
            results = run_evals(
                dataframe=spans_df,
                evaluators=[evaluator],
                provide_explanation=True,
            )
            if not results or len(results) == 0 or results[0].empty:
                logger.info(f"  ⚠️  {eval_name}: no results")
                continue

            result_df = results[0]
            logged = 0

            # Log each annotation individually via the new API
            for span_id, row in result_df.iterrows():
                try:
                    label = str(row.get("label", "")) if row.get("label") is not None else None
                    score = float(row.get("score")) if row.get("score") is not None else None
                    explanation = str(row.get("explanation", "")) if row.get("explanation") is not None else None

                    client.spans.add_span_annotation(
                        span_id=str(span_id),
                        annotation_name=eval_name,
                        annotator_kind="LLM",
                        label=label,
                        score=score,
                        explanation=explanation,
                    )
                    logged += 1
                except Exception as e:
                    logger.debug(f"    Failed to log span {span_id}: {e}")

            if logged > 0:
                logger.info(f"  ✅ {eval_name}: {logged}/{len(result_df)} spans annotated")
                success_count += 1
            else:
                logger.info(f"  ⚠️  {eval_name}: evaluated but failed to log")

        except Exception as e:
            logger.warning(f"  ❌ {eval_name} failed: {e}")

    logger.info(f"\n🎉 {success_count}/{len(evaluator_configs)} evaluations complete!")
    logger.info("   View results at http://localhost:6006")
    logger.info("   Click clarity-cx project → select a trace → see Annotations tab")


if __name__ == "__main__":
    main()
