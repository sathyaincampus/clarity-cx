"""
Clarity CX — AI-Powered Call Center Intelligence Platform
Main Streamlit Application
"""

import streamlit as st
import json
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Page config
st.set_page_config(
    page_title="Clarity CX — Call Center AI",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Root Variables */
    :root {
        --accent: #06b6d4;
        --accent-light: #67e8f9;
        --green: #22c55e;
        --orange: #f59e0b;
        --red: #ef4444;
        --purple: #a78bfa;
    }

    /* Global */
    .stApp {
        font-family: 'Inter', system-ui, sans-serif;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(167, 139, 250, 0.1));
        border: 1px solid rgba(6, 182, 212, 0.2);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .main-header h1 {
        font-size: 1.8em;
        font-weight: 700;
        background: linear-gradient(135deg, #67e8f9, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }

    .main-header p {
        color: #94a3b8;
        font-size: 0.9em;
        margin: 0;
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        border-color: rgba(6, 182, 212, 0.3);
        transform: translateY(-2px);
    }

    .metric-card .value {
        font-size: 2em;
        font-weight: 700;
        color: #67e8f9;
        line-height: 1.2;
    }

    .metric-card .label {
        font-size: 0.85em;
        color: #94a3b8;
        margin-top: 4px;
    }

    /* Score Badges */
    .score-excellent { color: #22c55e; }
    .score-good { color: #f59e0b; }
    .score-needs-work { color: #f97316; }
    .score-critical { color: #ef4444; }

    .badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 600;
    }

    .badge-green { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
    .badge-yellow { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
    .badge-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
    .badge-blue { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }

    /* Report Section */
    .report-section {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
    }

    .report-section h3 {
        color: #67e8f9;
        font-size: 1.1em;
        margin-bottom: 12px;
    }

    /* Sidebar */
    .sidebar-info {
        font-size: 0.85em;
        color: #94a3b8;
        padding: 8px 0;
    }

    /* Hide default Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Transcript viewer */
    .transcript-line {
        padding: 6px 12px;
        margin: 2px 0;
        border-radius: 8px;
        font-size: 0.9em;
    }
    .transcript-line:hover {
        background: rgba(255, 255, 255, 0.04);
    }
    .transcript-speaker {
        color: #67e8f9;
        font-weight: 600;
        margin-right: 8px;
    }
    .transcript-timestamp {
        color: #64748b;
        font-size: 0.8em;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)


def get_score_emoji(score: float) -> str:
    """Get emoji for score band"""
    if score >= 8.0:
        return "🟢"
    elif score >= 6.0:
        return "🟡"
    elif score >= 4.0:
        return "🟠"
    return "🔴"


def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <div>
            <h1>📞 Clarity CX</h1>
            <p>AI-Powered Call Center Intelligence Platform</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def load_sample_transcripts() -> list:
    """Load sample transcripts from data directory"""
    samples_path = Path(__file__).parent.parent.parent / "data" / "sample_transcripts" / "samples.json"
    if samples_path.exists():
        with open(samples_path, "r") as f:
            return json.load(f)
    return []


def format_transcript_text(transcript_data) -> str:
    """Convert transcript segments to readable text"""
    if isinstance(transcript_data, list):
        lines = []
        for seg in transcript_data:
            if isinstance(seg, dict):
                speaker = seg.get("speaker", "Unknown")
                text = seg.get("text", "")
                timestamp = seg.get("timestamp", "")
                lines.append(f"[{timestamp}] {speaker}: {text}")
        return "\n".join(lines)
    return str(transcript_data)


def render_dashboard_tab():
    """Dashboard tab with overview metrics"""
    st.header("📊 Dashboard")

    # Get live stats from database
    from src.database import get_db
    db = get_db()
    stats = db.get_dashboard_stats()

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Calls", str(stats["total_calls"]))
    with col2:
        st.metric("Avg QA Score", f"{stats['avg_score']}/10")
    with col3:
        st.metric("Resolution Rate", f"{stats['resolution_rate']}%")
    with col4:
        st.metric("Avg Handle Time", "1:22")

    st.divider()

    # Score distribution from DB
    dist = stats.get("score_distribution", {})
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Score Distribution")
        import plotly.graph_objects as go

        fig = go.Figure(data=[
            go.Bar(
                x=["🟢 Excellent", "🟡 Good", "🟠 Needs Work", "🔴 Critical"],
                y=[
                    dist.get("excellent", 0),
                    dist.get("good", 0),
                    dist.get("needs_work", 0),
                    dist.get("critical", 0),
                ],
                marker_color=["#22c55e", "#f59e0b", "#f97316", "#ef4444"],
            )
        ])
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=280,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Resolution Status")
        # Get resolution counts from DB
        history = db.get_call_history(limit=200)
        resolved = sum(1 for h in history if h.get("resolution_status") == "resolved")
        escalated = sum(1 for h in history if h.get("resolution_status") == "escalated")
        pending = sum(1 for h in history if h.get("resolution_status") in ("pending", "unresolved", None, ""))

        fig2 = go.Figure(data=[
            go.Pie(
                labels=["Resolved", "Escalated", "Pending"],
                values=[resolved, escalated, pending],
                marker_colors=["#22c55e", "#f59e0b", "#ef4444"],
                hole=0.5,
            )
        ])
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=280,
            showlegend=True,
            legend=dict(
                font=dict(color="#94a3b8"),
            ),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Recent calls from DB with sort & filter
    st.subheader("Recent Calls")
    history = db.get_call_history(limit=100)
    if history:
        # Filter and sort controls
        col_search, col_score_filter, col_status_filter, col_sort = st.columns([2, 1, 1, 1])
        with col_search:
            dash_search = st.text_input("🔍 Search", placeholder="Search by topic or agent...", key="dash_search")
        with col_score_filter:
            score_band = st.selectbox("Score Band", ["All", "🟢 Excellent (8+)", "🟡 Good (6-8)", "🟠 Needs Work (4-6)", "🔴 Critical (<4)"], key="dash_score")
        with col_status_filter:
            status_filter = st.selectbox("Status", ["All", "resolved", "escalated", "pending"], key="dash_status")
        with col_sort:
            sort_by = st.selectbox("Sort By", ["Newest First", "Oldest First", "Score ↑", "Score ↓"], key="dash_sort")

        # Apply filters
        filtered = []
        for call in history:
            score = call.get("overall_score", 0) or 0
            intent = call.get("customer_intent", "") or ""
            agent = call.get("agent_name", "") or ""
            resolution = call.get("resolution_status", "") or ""

            # Search filter
            if dash_search:
                search_target = f"{intent} {agent} {resolution}".lower()
                if dash_search.lower() not in search_target:
                    continue

            # Score band filter
            if score_band.startswith("🟢") and score < 8:
                continue
            elif score_band.startswith("🟡") and (score < 6 or score >= 8):
                continue
            elif score_band.startswith("🟠") and (score < 4 or score >= 6):
                continue
            elif score_band.startswith("🔴") and score >= 4:
                continue

            # Status filter
            if status_filter != "All" and resolution != status_filter:
                continue

            filtered.append(call)

        # Apply sorting
        if sort_by == "Score ↓":
            filtered.sort(key=lambda c: c.get("overall_score", 0) or 0, reverse=True)
        elif sort_by == "Score ↑":
            filtered.sort(key=lambda c: c.get("overall_score", 0) or 0)
        elif sort_by == "Oldest First":
            filtered.sort(key=lambda c: c.get("call_date", "") or "")
        # "Newest First" is the default DB order

        # Show count
        st.caption(f"Showing {len(filtered)} of {len(history)} calls")

        # Render filtered results
        for idx, call in enumerate(filtered, start=1):
            score = call.get("overall_score", 0) or 0
            emoji = get_score_emoji(score)
            col_num, col_a, col_b, col_c, col_d = st.columns([0.3, 3, 1, 1, 1])
            with col_num:
                st.caption(f"**{idx}**")
            with col_a:
                intent = call.get("customer_intent", "Call Analysis")
                agent = call.get("agent_name", "")
                label = f"**{intent}**" + (f" — Agent: {agent}" if agent else "")
                st.write(label)
            with col_b:
                st.write(f"{emoji} {score}/10")
            with col_c:
                resolution = call.get("resolution_status", "—")
                st.write(resolution or "—")
            with col_d:
                call_date = call.get("call_date", "") or ""
                st.caption(call_date[:10] if len(str(call_date)) >= 10 else "—")
    else:
        st.info("No calls analyzed yet. Go to the Analyze tab to get started!")


def render_analyze_tab():
    """Analyze tab — upload and analyze calls"""
    st.header("🎙️ Analyze Call")

    # Input method selection
    input_method = st.radio(
        "Input Method",
        ["📤 Upload Audio", "📝 Paste Transcript", "📁 Sample Transcript"],
        horizontal=True,
    )

    input_text = ""
    uploaded_file = None

    if input_method == "📤 Upload Audio":
        uploaded_file = st.file_uploader(
            "Upload audio file",
            type=["wav", "mp3", "flac", "m4a", "ogg"],
            help="Upload a call recording (WAV, MP3, FLAC, M4A, OGG)",
        )
        if uploaded_file:
            st.audio(uploaded_file)
            st.info("🎙️ Audio file ready for transcription via Gemini")

    elif input_method == "📝 Paste Transcript":
        input_text = st.text_area(
            "Paste call transcript",
            height=250,
            placeholder="Agent: Thank you for calling...\nCustomer: Hi, I'm calling about...",
        )

    elif input_method == "📁 Sample Transcript":
        samples = load_sample_transcripts()
        if samples:
            sample_names = [f"{s['scenario']} ({s['call_id']})" for s in samples]
            selected = st.selectbox("Select a sample call", sample_names)
            idx = sample_names.index(selected)
            sample = samples[idx]
            input_text = format_transcript_text(sample["transcript"])
            with st.expander("📜 View Transcript", expanded=False):
                for seg in sample["transcript"]:
                    st.markdown(
                        f"<span class='transcript-timestamp'>[{seg['timestamp']}]</span>"
                        f"<span class='transcript-speaker'>{seg['speaker']}:</span>"
                        f"{seg['text']}",
                        unsafe_allow_html=True,
                    )

    # LLM Configuration
    with st.sidebar:
        st.subheader("⚙️ LLM Settings")
        provider = st.selectbox(
            "Provider",
            ["google", "openai", "anthropic"],
            index=0,
        )
        model_map = {
            "google": ["gemini-2.0-flash", "gemini-1.5-pro"],
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "anthropic": ["claude-sonnet-4-20250514", "claude-3-haiku-20240307"],
        }
        model = st.selectbox("Model", model_map.get(provider, []))

    # Check if we have valid input (text or audio)
    has_input = bool(input_text) or bool(uploaded_file)

    # Analyze button
    col_btn, col_status = st.columns([1, 3])
    with col_btn:
        analyze_clicked = st.button(
            "🚀 Analyze Call",
            type="primary",
            use_container_width=True,
        )

    if analyze_clicked and not has_input:
        st.warning("⚠️ Please upload an audio file, paste a transcript, or select a sample before analyzing.")

    if analyze_clicked and has_input:
        with st.status("🔄 Running analysis pipeline...", expanded=True) as status:
            try:
                from src.orchestration.graph import analyze_call

                # Handle audio file upload
                input_path = ""
                if uploaded_file and not input_text:
                    import tempfile
                    st.write("🎙️ **Transcription Agent**: Preparing audio for transcription...")
                    # Save uploaded file to temp location
                    suffix = os.path.splitext(uploaded_file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        input_path = tmp.name
                    st.write(f"📁 Saved audio: {uploaded_file.name} ({uploaded_file.size / 1024:.0f}KB)")
                else:
                    st.write("📥 **Intake Agent**: Validating input...")

                # Run the pipeline
                result = asyncio.run(analyze_call(
                    input_path=input_path,
                    input_text=input_text,
                    llm_provider=provider,
                    llm_model=model,
                ))

                # Clean up temp file
                if input_path:
                    try:
                        os.unlink(input_path)
                    except OSError:
                        pass

                status.update(label="✅ Analysis Complete!", state="complete")
                st.session_state["last_result"] = result

                # Save to database for history/dashboard
                report = result.get("final_report", {})
                if report:
                    try:
                        from src.database import get_db
                        db = get_db()
                        call_id = db.save_analysis(report)
                        st.success(f"💾 Saved to call history (ID: {call_id[:8]}...)")
                        # Rerun so Dashboard and History tabs pick up the new data
                        st.rerun()
                    except Exception as save_err:
                        st.warning(f"⚠️ Analysis complete but failed to save to history: {save_err}")

            except Exception as e:
                status.update(label=f"❌ Error: {str(e)}", state="error")
                st.error(f"Analysis failed: {str(e)}")
                st.info(
                    "💡 Make sure your API keys are set in the `.env` file. "
                    "Copy `.env.example` to `.env` and add your keys."
                )

    # Display results
    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        report = result.get("final_report", {})

        if report:
            _render_report(report)


def _render_report(report: dict):
    """Render the analysis report"""
    st.divider()
    st.subheader("📋 Analysis Report")

    status = report.get("status", "unknown")
    status_emoji = "✅" if status == "complete" else "⚠️" if status == "partial" else "❌"
    st.caption(f"{status_emoji} Status: {status} | {report.get('report_id', '')} | {report.get('generated_at', '')}")

    # Summary section
    summary = report.get("summary", {})
    if summary:
        st.markdown("### 📝 Call Summary")
        st.write(summary.get("summary", "No summary available"))

        col_intent, col_resolution = st.columns(2)
        with col_intent:
            st.info(f"🎯 **Intent:** {summary.get('customer_intent', 'N/A')}")
        with col_resolution:
            res_status = summary.get("resolution_status", "pending")
            res_emoji = "✅" if res_status == "resolved" else "⚠️" if res_status == "escalated" else "🔄"
            st.info(f"{res_emoji} **Resolution:** {res_status}")

        # Key points
        key_points = summary.get("key_points", [])
        if key_points:
            st.markdown("**Key Points:**")
            for kp in key_points:
                st.write(f"• {kp}")

        # Action items
        actions = summary.get("action_items", [])
        if actions:
            st.markdown("**Action Items:**")
            for action in actions:
                st.write(f"☑️ {action}")

        # Topics
        topics = summary.get("topics", [])
        if topics:
            st.write("**Topics:** " + " · ".join(f"`{t}`" for t in topics))

    st.divider()

    # Quality scores section
    quality = report.get("quality_scores", {})
    if quality and quality.get("overall_score", 0) > 0:
        st.markdown("### 📊 Quality Assessment")

        overall = quality.get("overall_score", 0)
        band = quality.get("band", {})
        band_emoji = band.get("emoji", "⚪")
        band_label = band.get("label", "Not scored")

        # Overall score display
        st.metric(
            f"{band_emoji} Overall Quality Score",
            f"{overall:.1f} / 10",
            delta=band_label,
        )

        # Dimension scores
        dims = [
            ("Empathy (25%)", quality.get("empathy", {})),
            ("Resolution (25%)", quality.get("resolution", {})),
            ("Professionalism (20%)", quality.get("professionalism", {})),
            ("Compliance (15%)", quality.get("compliance", {})),
            ("Efficiency (15%)", quality.get("efficiency", {})),
        ]

        for dim_name, dim_data in dims:
            if isinstance(dim_data, dict):
                score = dim_data.get("score", 0)
                justification = dim_data.get("justification", "")
                emoji = get_score_emoji(score)
                st.write(f"{emoji} **{dim_name}:** {score:.1f}/10 — {justification}")

        # Radar chart
        import plotly.graph_objects as go
        fig = go.Figure()
        categories = ["Empathy", "Resolution", "Professionalism", "Compliance", "Efficiency"]
        values = [
            quality.get("empathy", {}).get("score", 0),
            quality.get("resolution", {}).get("score", 0),
            quality.get("professionalism", {}).get("score", 0),
            quality.get("compliance", {}).get("score", 0),
            quality.get("efficiency", {}).get("score", 0),
        ]
        values.append(values[0])  # Close the polygon
        categories.append(categories[0])

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            fillcolor="rgba(6, 182, 212, 0.2)",
            line=dict(color="#06b6d4", width=2),
            name="Score",
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], color="#64748b"),
                bgcolor="rgba(0,0,0,0)",
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            margin=dict(l=60, r=60, t=40, b=40),
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Flags and recommendations
        flags = quality.get("flags", [])
        if flags:
            st.warning("⚠️ **Flags:** " + ", ".join(flags))

        recs = quality.get("recommendations", [])
        if recs:
            st.info("💡 **Recommendations:**")
            for rec in recs:
                st.write(f"• {rec}")


def render_history_tab():
    """Call history tab — reads from database"""
    st.header("📋 Call History")

    from src.database import get_db
    db = get_db()
    history = db.get_call_history(limit=50)

    if not history:
        st.info("No call history yet. Analyze some calls or run `python scripts/seed_database.py` to load sample data!")
        return

    # Filter controls
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search = st.text_input("🔍 Search calls", placeholder="Search by topic or agent...")
    with col_filter:
        filter_score = st.selectbox("Filter by score", ["All", "🟢 Excellent", "🟡 Good", "🟠 Needs Work", "🔴 Critical"])

    # Display history from DB
    for call in history:
        intent = call.get("customer_intent", "") or "Call Analysis"
        summary_text = call.get("summary", "") or ""
        agent_name = call.get("agent_name", "") or ""
        score = call.get("overall_score", 0) or 0

        # Search filter
        search_target = f"{intent} {summary_text} {agent_name}".lower()
        if search and search.lower() not in search_target:
            continue

        # Score filter
        if filter_score != "All":
            if filter_score.startswith("🟢") and score < 8:
                continue
            elif filter_score.startswith("🟡") and (score < 6 or score >= 8):
                continue
            elif filter_score.startswith("🟠") and (score < 4 or score >= 6):
                continue
            elif filter_score.startswith("🔴") and score >= 4:
                continue

        emoji = get_score_emoji(score)
        resolution = call.get("resolution_status", "—") or "—"
        call_date = call.get("call_date", "") or "—"
        label = f"{emoji} **{intent}** — Score: {score}/10 | {resolution}"
        if agent_name:
            label += f" | Agent: {agent_name}"

        with st.expander(label):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                if summary_text:
                    st.write("**Summary:**")
                    st.write(summary_text)
                else:
                    st.caption("No summary available")
            with col_b:
                st.metric("QA Score", f"{score}/10")
                st.caption(f"📅 {call_date[:10] if len(str(call_date)) >= 10 else call_date}")
                st.caption(f"📊 Status: {resolution}")
                duration = call.get("duration_seconds", 0) or 0
                if duration > 0:
                    mins = duration // 60
                    secs = duration % 60
                    st.caption(f"⏱️ {mins}:{secs:02d}")


def render_trends_tab():
    """Trends tab with analytics — data-driven from database"""
    st.header("📈 Trends & Analytics")

    from src.database import get_db
    import plotly.graph_objects as go

    db = get_db()
    trends = db.get_trends_data()

    daily = trends.get("daily_scores", [])
    dims = trends.get("dimension_averages", {})
    topics = trends.get("top_topics", [])

    if not daily and not dims:
        st.info("No trend data yet. Analyze some calls or run `python scripts/seed_database.py` to load sample data!")
        return

    # Score trends over time
    st.subheader("Quality Score Trend")
    if daily:
        days = [d["day"] for d in daily]
        scores = [d["avg_score"] for d in daily]
        counts = [d["count"] for d in daily]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days,
            y=scores,
            mode="lines+markers",
            line=dict(color="#06b6d4", width=3),
            fill="tozeroy",
            fillcolor="rgba(6, 182, 212, 0.1)",
            name="Avg Score",
            text=[f"{s}/10 ({c} calls)" for s, c in zip(scores, counts)],
            hoverinfo="text+x",
        ))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            margin=dict(l=40, r=20, t=20, b=40),
            height=300,
            yaxis=dict(range=[0, 10], showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No daily score data available yet.")

    # Dimension comparison + Topics
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Dimension Averages")
        if dims:
            dim_names = ["Empathy", "Resolution", "Profess.", "Compliance", "Efficiency"]
            dim_values = [
                dims.get("empathy", 0),
                dims.get("resolution", 0),
                dims.get("professionalism", 0),
                dims.get("compliance", 0),
                dims.get("efficiency", 0),
            ]
            fig2 = go.Figure(data=[
                go.Bar(
                    x=dim_names,
                    y=dim_values,
                    marker_color=["#06b6d4", "#22c55e", "#a78bfa", "#f59e0b", "#3b82f6"],
                    text=[f"{v:.1f}" for v in dim_values],
                    textposition="auto",
                )
            ])
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Inter"),
                margin=dict(l=20, r=20, t=20, b=40),
                height=280,
                yaxis=dict(range=[0, 10], showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                xaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("No dimension data available yet.")

    with col2:
        st.subheader("Top Topics")
        if topics:
            topic_names = [t[0] for t in topics]
            topic_counts = [t[1] for t in topics]
            fig3 = go.Figure(data=[
                go.Bar(
                    x=topic_counts,
                    y=topic_names,
                    orientation="h",
                    marker_color="#a78bfa",
                    text=topic_counts,
                    textposition="auto",
                )
            ])
            fig3.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Inter"),
                margin=dict(l=100, r=20, t=20, b=40),
                height=280,
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=False, autorange="reversed"),
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.caption("No topic data available yet.")


def render_settings_tab():
    """Settings tab"""
    st.header("⚙️ Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("LLM Configuration")
        st.selectbox("Default Provider", ["google", "openai", "anthropic"], key="settings_provider")
        st.number_input("Temperature", min_value=0.0, max_value=2.0, value=0.3, step=0.1)
        st.number_input("Max Tokens", min_value=100, max_value=16384, value=4096, step=256)

        st.subheader("Whisper Settings")
        st.selectbox("Model", ["whisper-1"], key="whisper_model")
        st.selectbox("Language", ["en (English)", "es (Spanish)", "fr (French)", "de (German)"])

    with col2:
        st.subheader("Quality Scoring")
        st.slider("Empathy Weight", 0.0, 1.0, 0.25, key="empathy_weight")
        st.slider("Resolution Weight", 0.0, 1.0, 0.25, key="resolution_weight")
        st.slider("Professionalism Weight", 0.0, 1.0, 0.20, key="prof_weight")
        st.slider("Compliance Weight", 0.0, 1.0, 0.15, key="compliance_weight")
        st.slider("Efficiency Weight", 0.0, 1.0, 0.15, key="efficiency_weight")

    st.divider()

    st.subheader("API Keys Status")
    keys = {
        "Google": os.getenv("GOOGLE_API_KEY"),
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "Phoenix": "yes" if os.getenv("PHOENIX_ENABLED", "true").lower() == "true" else None,
    }
    for name, key in keys.items():
        status = "✅ Configured" if key else "❌ Not set"
        st.write(f"**{name}:** {status}")

    st.divider()
    st.subheader("About")
    st.write("**Clarity CX** v1.0.0")
    st.write("AI-Powered Call Center Intelligence Platform")
    st.write("Built with LangGraph, Gemini, Arize Phoenix, Streamlit")


# ─── Main App ─────────────────────────────────────────────
def main():
    render_header()

    # Tab navigation
    tab_dashboard, tab_analyze, tab_history, tab_trends, tab_settings = st.tabs([
        "📊 Dashboard",
        "🎙️ Analyze Call",
        "📋 Call History",
        "📈 Trends",
        "⚙️ Settings",
    ])

    with tab_dashboard:
        render_dashboard_tab()

    with tab_analyze:
        render_analyze_tab()

    with tab_history:
        render_history_tab()

    with tab_trends:
        render_trends_tab()

    with tab_settings:
        render_settings_tab()


if __name__ == "__main__":
    main()
