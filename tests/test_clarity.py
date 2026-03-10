"""Tests for Clarity CX agents and pipeline"""

import pytest
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIntakeAgent:
    """Tests for the Call Intake Agent"""

    @pytest.mark.asyncio
    async def test_text_input_valid(self):
        """Test valid text input processing"""
        from src.agents.intake_agent import IntakeAgent

        agent = IntakeAgent()
        state = {
            "input_text": "Agent: Thank you for calling support. How may I help you today?\n"
                         "Customer: I need help with my order, it hasn't arrived yet.\n"
                         "Agent: I'm sorry to hear that. Let me look into this for you.",
            "input_path": "",
        }
        result = await agent.process(state)
        assert result["input_type"] == "text"
        assert result["call_metadata"]["format"] == "text"
        assert result["call_metadata"]["word_count"] > 0
        assert result["transcript"] is not None

    @pytest.mark.asyncio
    async def test_text_input_too_short(self):
        """Test rejection of too-short text"""
        from src.agents.intake_agent import IntakeAgent

        agent = IntakeAgent()
        state = {"input_text": "Hi", "input_path": ""}
        with pytest.raises(ValueError, match="too short"):
            await agent.process(state)

    @pytest.mark.asyncio
    async def test_json_input(self):
        """Test JSON transcript input"""
        from src.agents.intake_agent import IntakeAgent

        agent = IntakeAgent()
        json_input = json.dumps({
            "transcript": [
                {"speaker": "Agent", "text": "Thank you for calling, how may I help?"},
                {"speaker": "Customer", "text": "I need help with my billing."},
            ]
        })
        state = {"input_text": json_input, "input_path": ""}
        result = await agent.process(state)
        assert result["input_type"] == "transcript"
        assert result["call_metadata"]["has_speaker_labels"] is True

    @pytest.mark.asyncio
    async def test_no_input_raises_error(self):
        """Test error when no input provided"""
        from src.agents.intake_agent import IntakeAgent

        agent = IntakeAgent()
        state = {"input_text": "", "input_path": ""}
        with pytest.raises(ValueError, match="No input provided"):
            await agent.process(state)


class TestTranscriptionAgent:
    """Tests for the Transcription Agent"""

    @pytest.mark.asyncio
    async def test_skip_for_text_input(self):
        """Test that transcription is skipped for text input"""
        from src.agents.transcription_agent import TranscriptionAgent

        agent = TranscriptionAgent()
        state = {
            "input_type": "text",
            "transcript": "Agent: Hello!\nCustomer: Hi!",
            "speaker_segments": [],
        }
        result = await agent.process(state)
        assert result["transcript"] == "Agent: Hello!\nCustomer: Hi!"

    @pytest.mark.asyncio
    async def test_skip_for_transcript_input(self):
        """Test that transcription is skipped for JSON transcript input"""
        from src.agents.transcription_agent import TranscriptionAgent

        agent = TranscriptionAgent()
        state = {
            "input_type": "transcript",
            "transcript": "Speaker A: Test",
            "speaker_segments": [{"speaker": "A", "text": "Test"}],
        }
        result = await agent.process(state)
        assert result["transcript"] == "Speaker A: Test"


class TestBaseAgent:
    """Tests for the Base Agent class"""

    @pytest.mark.asyncio
    async def test_safe_process_success(self):
        """Test safe_process wraps results correctly"""
        from src.agents.intake_agent import IntakeAgent

        agent = IntakeAgent()
        state = {
            "input_text": "Agent: Thank you for calling customer support. How can I help you?\n"
                         "Customer: I need to check on my delivery status please.",
            "input_path": "",
        }
        result = await agent.safe_process(state)
        assert "agent_outputs" in result
        assert result["agent_outputs"][0]["agent"] == "IntakeAgent"
        assert result["agent_outputs"][0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_safe_process_error(self):
        """Test safe_process handles errors"""
        from src.agents.intake_agent import IntakeAgent

        agent = IntakeAgent()
        state = {"input_text": "", "input_path": ""}
        result = await agent.safe_process(state)
        assert result["agent_outputs"][0]["status"] == "error"
        assert "error_log" in result


class TestQualityScoringModels:
    """Tests for Quality Scoring Pydantic models"""

    def test_score_band_excellent(self):
        from src.agents.quality_score_agent import get_score_band
        band = get_score_band(9.0)
        assert band["label"] == "Excellent"
        assert band["emoji"] == "🟢"

    def test_score_band_good(self):
        from src.agents.quality_score_agent import get_score_band
        band = get_score_band(7.0)
        assert band["label"] == "Good"
        assert band["emoji"] == "🟡"

    def test_score_band_needs_work(self):
        from src.agents.quality_score_agent import get_score_band
        band = get_score_band(5.0)
        assert band["label"] == "Needs Improvement"
        assert band["emoji"] == "🟠"

    def test_score_band_critical(self):
        from src.agents.quality_score_agent import get_score_band
        band = get_score_band(2.0)
        assert band["label"] == "Critical"
        assert band["emoji"] == "🔴"


class TestSummarizationModels:
    """Tests for Summarization Pydantic models"""

    def test_call_summary_model(self):
        from src.agents.summarization_agent import CallSummary
        summary = CallSummary(
            summary="Customer called about billing issue.",
            key_points=["Double charge identified", "Refund processed"],
            action_items=["Send confirmation email"],
            customer_intent="Billing dispute",
            resolution_status="resolved",
            topics=["billing"],
            sentiment_trajectory="negative_to_positive",
        )
        assert summary.resolution_status == "resolved"
        assert len(summary.key_points) == 2


class TestPIIDetection:
    """Tests for PII detection MCP tool"""

    @pytest.mark.asyncio
    async def test_detect_ssn(self):
        from src.mcp.tools.qa_tools import detect_pii
        result = await detect_pii("My SSN is 123-45-6789")
        assert result["pii_found"] is True
        assert result["risk_level"] == "critical"

    @pytest.mark.asyncio
    async def test_detect_credit_card(self):
        from src.mcp.tools.qa_tools import detect_pii
        result = await detect_pii("Card: 4111-1111-1111-1111")
        assert result["pii_found"] is True

    @pytest.mark.asyncio
    async def test_detect_email(self):
        from src.mcp.tools.qa_tools import detect_pii
        result = await detect_pii("Email me at john@example.com")
        assert result["pii_found"] is True

    @pytest.mark.asyncio
    async def test_no_pii(self):
        from src.mcp.tools.qa_tools import detect_pii
        result = await detect_pii("Thank you for calling, have a great day!")
        assert result["pii_found"] is False
        assert result["risk_level"] == "none"


class TestComplianceCheck:
    """Tests for compliance checking MCP tool"""

    @pytest.mark.asyncio
    async def test_full_compliance(self):
        from src.mcp.tools.qa_tools import check_compliance
        transcript = (
            "Thank you for calling Acme Support. How may I help you today? "
            "Is there anything else I can help with? Have a great day!"
        )
        result = await check_compliance(transcript)
        assert result["compliance_rate"] > 0
        assert result["overall_status"] in ("pass", "review")

    @pytest.mark.asyncio
    async def test_violation_detection(self):
        from src.mcp.tools.qa_tools import check_compliance
        transcript = "I don't care about your problem. Whatever."
        result = await check_compliance(transcript)
        assert len(result["violations"]) > 0


class TestOrchestrationState:
    """Tests for LangGraph state management"""

    def test_create_initial_state(self):
        # Load state module directly to avoid langgraph import in __init__.py
        import importlib.util
        state_path = str(Path(__file__).parent.parent / "src" / "orchestration" / "state.py")
        spec = importlib.util.spec_from_file_location("orchestration_state", state_path)
        state_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(state_mod)

        state = state_mod.create_initial_state(
            input_text="Hello",
            llm_provider="openai",
            llm_model="gpt-4o",
        )
        assert state["input_text"] == "Hello"
        assert state["llm_provider"] == "openai"
        assert state["agent_outputs"] == []
        assert state["error_log"] == []
        assert state["session_id"]  # Should be generated


class TestDatabaseInit:
    """Tests for database initialization"""

    def test_create_database(self, tmp_path):
        from src.database import Database
        db_path = str(tmp_path / "test.db")
        db = Database(db_path)
        assert os.path.exists(db_path)

    def test_get_empty_history(self, tmp_path):
        from src.database import Database
        db = Database(str(tmp_path / "test.db"))
        history = db.get_call_history()
        assert history == []

    def test_get_empty_stats(self, tmp_path):
        from src.database import Database
        db = Database(str(tmp_path / "test.db"))
        stats = db.get_dashboard_stats()
        assert stats["total_calls"] == 0
        assert stats["avg_score"] == 0


class TestSampleData:
    """Tests for sample transcript data"""

    def test_samples_exist(self):
        path = Path(__file__).parent.parent / "data" / "sample_transcripts" / "samples.json"
        assert path.exists()

    def test_samples_valid_json(self):
        path = Path(__file__).parent.parent / "data" / "sample_transcripts" / "samples.json"
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) >= 6

    def test_sample_structure(self):
        path = Path(__file__).parent.parent / "data" / "sample_transcripts" / "samples.json"
        with open(path) as f:
            data = json.load(f)

        for sample in data:
            assert "call_id" in sample
            assert "scenario" in sample
            assert "expected_score" in sample
            assert "transcript" in sample
            assert isinstance(sample["transcript"], list)
            for entry in sample["transcript"]:
                assert "speaker" in entry
                assert "text" in entry


# Need os for tmp_path usage
import os
