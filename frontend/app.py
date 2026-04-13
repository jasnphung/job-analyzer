import streamlit as st
import pandas as pd
import json
import re
import time
import threading
import urllib.parse

from scripts.analyze import build_pipeline, process_jobs

# ==============================================================================
#  Page config
# ==============================================================================
st.set_page_config(
    page_title="Job Posting Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
#  Theme & styling
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --bg: #0a0e14;
        --surface: #111822;
        --surface-2: #0d131b;
        --border: #1e2936;
        --border-hi: #2c3e52;
        --text: #e2e8f0;
        --text-muted: #64748b;
        --text-dim: #94a3b8;
        --heading: #f1f5f9;
        --accent: #7dd3fc;
        --accent-dim: #0ea5e9;
        --success: #34d399;
        --success-bg: #052e20;
        --warn: #fbbf24;
        --danger: #f87171;
        --violet: #a78bfa;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, sans-serif;
        background: var(--bg);
        color: var(--text);
    }
    h1, h2, h3, h4, h5 {
        font-family: 'Inter', sans-serif !important;
        color: var(--heading) !important;
        letter-spacing: -0.02em;
        font-weight: 600;
    }
    code, .mono { font-family: 'JetBrains Mono', monospace; }

    /* Main container width */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }

    /* Inputs */
    .stTextArea textarea, .stTextInput input, .stSelectbox > div > div {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px !important;
        background-color: var(--surface-2) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(125, 211, 252, 0.12) !important;
    }

    /* Buttons */
    .stButton > button, .stDownloadButton > button {
        background-color: var(--surface);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all 0.15s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: var(--surface);
        border-color: var(--border-hi);
        color: var(--heading);
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #0ea5e9, #0284c7);
        border-color: #0ea5e9;
        color: white;
        font-weight: 600;
        box-shadow: 0 1px 0 rgba(255,255,255,0.1) inset, 0 2px 8px rgba(14,165,233,0.25);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #38bdf8, #0ea5e9);
        border-color: #38bdf8;
    }
    .stButton > button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    /* Header bar */
    .header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 0 20px 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 28px;
    }
    .header-title {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .header-title h1 {
        font-size: 22px !important;
        margin: 0 !important;
        font-weight: 700 !important;
    }
    .header-title .subtitle {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 2px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Status chip */
    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .status-chip .dot {
        width: 6px; height: 6px; border-radius: 50%;
    }
    .status-on  { background: rgba(52,211,153,0.1); color: var(--success); border: 1px solid rgba(52,211,153,0.3); }
    .status-on .dot  { background: var(--success); box-shadow: 0 0 6px var(--success); }
    .status-off { background: rgba(248,113,113,0.08); color: var(--danger); border: 1px solid rgba(248,113,113,0.25); }
    .status-off .dot { background: var(--danger); }

    /* Panel / card */
    .panel {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 18px 20px;
    }
    .panel-title {
        display: flex; align-items: center; gap: 10px;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-muted);
        margin-bottom: 14px;
        font-weight: 600;
    }
    .panel-title .num {
        display: inline-flex; align-items: center; justify-content: center;
        width: 20px; height: 20px;
        background: var(--surface-2);
        border: 1px solid var(--border);
        border-radius: 4px;
        color: var(--accent);
        font-size: 11px;
    }

    /* URL chips */
    .url-chips {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 6px;
        margin-top: 10px;
    }
    .url-chip {
        background: rgba(125,211,252,0.06);
        border: 1px solid rgba(125,211,252,0.2);
        color: #bae6fd;
        padding: 4px 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        border-radius: 4px;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .url-counter {
        display: flex; align-items: center; gap: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 12px;
    }
    .url-counter .n { color: var(--accent); font-weight: 600; font-size: 13px; }
    .url-counter .empty { color: var(--text-muted); font-style: italic; }

    /* Metric tiles */
    .metric-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
    .metric-tile {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px 16px;
        position: relative;
        overflow: hidden;
    }
    .metric-tile::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: var(--accent-dim); opacity: 0.6;
    }
    .metric-tile.tile-success::before { background: var(--success); }
    .metric-tile.tile-violet::before { background: var(--violet); }
    .metric-tile.tile-warn::before { background: var(--warn); }
    .metric-label {
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--heading);
        line-height: 1;
    }
    .metric-sub {
        font-size: 11px;
        color: var(--text-muted);
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Job card */
    .job-card-head {
        display: flex; align-items: flex-start; justify-content: space-between;
        gap: 14px;
    }
    .job-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--heading);
        line-height: 1.4;
    }
    .job-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: var(--text-muted);
        background: var(--surface-2);
        border: 1px solid var(--border);
        padding: 2px 8px;
        border-radius: 4px;
        margin-left: 6px;
    }

    /* Meta grid */
    .meta-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px 24px;
        margin-top: 14px;
    }
    .meta-item { display: flex; flex-direction: column; gap: 2px; }
    .meta-k {
        font-size: 10px;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .meta-v { font-size: 13px; color: var(--text); word-break: break-word; }
    .meta-v a { color: var(--accent); text-decoration: none; }
    .meta-v a:hover { text-decoration: underline; }

    /* Classification pill strip */
    .pill-strip {
        display: flex; flex-wrap: wrap; gap: 6px;
        margin: 4px 0;
    }
    .pill {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 4px 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        font-weight: 500;
        border-radius: 4px;
        border: 1px solid;
        white-space: nowrap;
    }
    .pill-yes { background: rgba(52,211,153,0.08); border-color: rgba(52,211,153,0.3); color: var(--success); }
    .pill-no  { background: rgba(100,116,139,0.08); border-color: rgba(100,116,139,0.25); color: var(--text-dim); }
    .pill-lang { background: rgba(167,139,250,0.08); border-color: rgba(167,139,250,0.3); color: var(--violet); }
    .pill .ico { font-size: 10px; opacity: 0.9; }

    /* Description block */
    .description-block {
        font-size: 13px;
        line-height: 1.65;
        color: var(--text);
        padding: 4px 2px;
    }
    .description-block p { margin: 0 0 10px; }
    .description-block h1, .description-block h2, .description-block h3, .description-block h4 {
        font-size: 13px !important;
        font-weight: 600 !important;
        margin: 14px 0 6px !important;
        color: var(--heading) !important;
    }
    .description-block ul, .description-block ol { margin: 6px 0 10px 20px; }
    .description-block li { margin-bottom: 4px; }
    .description-block a { color: var(--accent); }

    /* Expanders */
    div[data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        background: var(--surface) !important;
        overflow: hidden;
    }
    div[data-testid="stExpander"] summary {
        padding: 12px 16px !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-testid="stExpander"] summary:hover {
        background: var(--surface-2);
    }
    div[data-testid="stExpander"] div[data-testid="stExpander"] {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        margin-top: 10px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--surface-2);
        padding: 4px;
        border-radius: 8px;
        border: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: var(--text-muted);
        font-size: 13px;
        font-weight: 500;
        padding: 6px 14px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: var(--surface) !important;
        color: var(--heading) !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }

    /* Dividers & misc */
    hr, [data-testid="stDivider"] {
        border-color: var(--border) !important;
        margin: 20px 0 !important;
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 48px 20px;
        border: 1px dashed var(--border);
        border-radius: 10px;
        background: var(--surface-2);
    }
    .empty-state .emoji { font-size: 36px; margin-bottom: 10px; }
    .empty-state .title { font-size: 15px; color: var(--heading); font-weight: 600; margin-bottom: 6px; }
    .empty-state .desc { font-size: 13px; color: var(--text-muted); }

    /* Sidebar hidden — all controls live in the main area */
    section[data-testid="stSidebar"] { display: none !important; }
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="collapsedControl"] { display: none !important; }

    /* Controls row */
    .controls-row {
        display: flex; align-items: center; justify-content: space-between;
        gap: 12px;
        margin-bottom: 18px;
    }

    /* Hide only the "Made with Streamlit" footer; keep the top-right menu visible */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
#  Session state
# ==============================================================================
if "results" not in st.session_state:
    st.session_state.results = None
if "pipeline" not in st.session_state:
    st.session_state.pipeline = None
if "url_input" not in st.session_state:
    st.session_state.url_input = ""
if "filter_query" not in st.session_state:
    st.session_state.filter_query = ""

def _clear_urls():
    st.session_state.url_input = ""

def _clear_results():
    st.session_state.results = None

# ==============================================================================
#  URL extraction
# ==============================================================================
URL_RE = re.compile(r"https?://[^\s,;<>\"'\]]+")

def extract_urls(text: str):
    if not text:
        return []
    return [u.rstrip(").,;") for u in URL_RE.findall(text)]

# ==============================================================================
#  Header
# ==============================================================================
pipe_status = (
    '<span class="status-chip status-on"><span class="dot"></span>Pipeline Online</span>'
    if st.session_state.pipeline
    else '<span class="status-chip status-off"><span class="dot"></span>Pipeline Offline</span>'
)
st.markdown(f"""
<div class="header">
    <div class="header-title">
        <div>
            <h1>Job Posting Analyzer</h1>
            <div class="subtitle">Workday postings to structured data</div>
        </div>
    </div>
    <div>{pipe_status}</div>
</div>
""", unsafe_allow_html=True)

# --- Pipeline control (main area; replaces former sidebar) ---
load_btn = st.button(
    "Load Pipeline" if not st.session_state.pipeline else "Reload Pipeline",
    width="stretch",
    type="primary" if not st.session_state.pipeline else "secondary",
    key="btn_load_pipeline",
)
if load_btn:
    with st.spinner("Initialising pipeline..."):
        st.session_state.pipeline = build_pipeline()
    st.toast("Pipeline ready")
    st.rerun()

# ==============================================================================
#  Input section
# ==============================================================================
st.markdown('<div class="panel-title">Input</div>', unsafe_allow_html=True)

# Live detection: runs on every rerun. The JS snippet below forces st.text_area
# to commit its value on every typing pause (~250ms debounce), so session_state
# tracks the current textarea content live instead of only on blur.
_current_urls = extract_urls(st.session_state.get("url_input", ""))

input_col, action_col = st.columns([4, 1], gap="medium")

with input_col:
    _pipeline_ready = bool(st.session_state.pipeline)
    st.text_area(
        "urls",
        key="url_input",
        placeholder=(
            "Paste URLs any way you like — newlines, commas, spaces, or mixed prose.\n\n"
            "e.g.\nhttps://uottawa.wd3.myworkdayjobs.com/...\nhttps://uottawa.wd3.myworkdayjobs.com/..."
        ) if _pipeline_ready else "Click Load Pipeline above to enable URL input.",
        height=170,
        label_visibility="collapsed",
        disabled=not _pipeline_ready,
    )

    # if _current_urls:
    #     chips_html = "".join(
    #         f'<span class="url-chip" title="{u}">{(u[:58] + "…") if len(u) > 58 else u}</span>'
    #         for u in _current_urls
    #     )
    #     st.markdown(
    #         '<div class="url-counter">URLs detected</div>'
    #         f'<div class="url-chips">{chips_html}</div>',
    #         unsafe_allow_html=True,
    #     )
    # else:
    #     st.markdown(
    #         '<div class="url-counter"><span class="empty">No URLs detected yet — paste at least one link above.</span></div>',
    #         unsafe_allow_html=True,
    #     )

with action_col:
    run_button = st.button(
        f"Analyze{f' ({len(_current_urls)})' if _current_urls else ''}",
        width="stretch",
        type="primary",
        disabled=not (_current_urls and st.session_state.pipeline),
        help=(None if (_current_urls and st.session_state.pipeline)
              else ("Load the pipeline first." if not st.session_state.pipeline
                    else "Paste at least one URL.")),
        key="btn_analyze",
    )
    st.button("Clear URLs", width="stretch",
              on_click=_clear_urls, key="btn_clear_urls",
              disabled=not st.session_state.get("url_input"))
    st.button("Reset Results", width="stretch",
              on_click=_clear_results, key="btn_clear_results",
              disabled=not st.session_state.results)

# --- Live-commit JS: force Streamlit's text_area to sync on each typing pause.
# Streamlit's text_area normally only commits on blur, so the chip count lags
# while the user is typing. The snippet finds the textarea in the parent
# document and, on each input pause, triggers blur+refocus (preserving the
# caret) which forces a commit and a rerun.
# NOTE: served via st.iframe using a data: URL per project convention.
# Data-URL iframes are cross-origin to the Streamlit parent, so parent-DOM
# access only works when the browser treats them as same-origin (Chromium-
# family + Streamlit's sandbox flags do). If a browser blocks it, the live
# count gracefully falls back to Streamlit's default blur-commit behaviour.
_live_commit_html = """<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>
<script>
(function() {
    try {
        const parentDoc = window.parent.document;
        function attach() {
            const tas = parentDoc.querySelectorAll('textarea[aria-label="urls"]');
            tas.forEach(function(ta) {
                if (ta.__liveCommit) return;
                ta.__liveCommit = true;
                let timer = null;
                ta.addEventListener('input', function() {
                    if (timer) clearTimeout(timer);
                    timer = setTimeout(function() {
                        const s = ta.selectionStart, e = ta.selectionEnd;
                        ta.blur();
                        ta.focus();
                        try { ta.setSelectionRange(s, e); } catch (err) {}
                    }, 250);
                });
            });
        }
        attach();
        new MutationObserver(attach).observe(parentDoc.body, { subtree: true, childList: true });
    } catch (e) { /* cross-origin: fall back to default blur-commit */ }
})();
</script>
</body></html>"""
st.markdown(
    "<style>iframe[src^='data:text/html']{display:none!important;}</style>",
    unsafe_allow_html=True,
)
st.iframe(
    "data:text/html;charset=utf-8," + urllib.parse.quote(_live_commit_html),
    height=1,
)

# Extract URLs at analyze-time from the committed value.
urls = _current_urls if run_button else []
if run_button and not urls:
    st.warning("No valid URLs detected in your input.")

# ==============================================================================
#  Run pipeline (per-URL progress)
# ==============================================================================
if run_button and urls and st.session_state.pipeline:
    _pipeline = st.session_state.pipeline
    _t_start = time.perf_counter()
    progress = st.progress(0.0, text="Starting analysis... 0.0s")
    collected = []
    fatal_error = None

    # Each URL is processed on a worker thread so the main Streamlit thread can
    # tick the progress bar every ~100ms, giving a truly live elapsed-time
    # counter instead of updating only once per completed job.
    for i, u in enumerate(urls):
        holder = {"done": False, "result": None, "error": None}

        def _worker(url=u, pipe=_pipeline, h=holder):
            try:
                h["result"] = process_jobs([url], pipe)
            except Exception as exc:
                h["error"] = exc
            finally:
                h["done"] = True

        worker = threading.Thread(target=_worker, daemon=True)
        worker.start()

        while not holder["done"]:
            _elapsed = time.perf_counter() - _t_start
            progress.progress(
                i / len(urls),
                text=(f"Analyzing {i + 1} of {len(urls)} "
                      f"- {u[:70]}{'...' if len(u) > 70 else ''}  {_elapsed:0.1f}s"),
            )
            time.sleep(0.1)
        worker.join()

        if holder["error"] is not None:
            fatal_error = holder["error"]
            break
        collected.extend(holder["result"] or [])

    if fatal_error is not None:
        st.error(f"Analysis failed: {fatal_error}")
    else:
        _elapsed = time.perf_counter() - _t_start
        progress.progress(
            1.0,
            text=f"Done - {len(collected)} posting(s) analyzed in {_elapsed:0.1f}s",
        )
        st.session_state.results = collected
        st.session_state.last_elapsed = _elapsed
        st.toast(f"Analyzed {len(collected)} posting(s) in {_elapsed:0.1f}s")

# ==============================================================================
#  Results
# ==============================================================================
if st.session_state.results:
    results = st.session_state.results
    df = pd.DataFrame(results)

    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Results · Classification</div>',
                unsafe_allow_html=True)

    # --- Metric tiles ---
    total = len(df)
    hs = int(df["health_science_related"].eq("Yes").sum())
    ma = int(df["masters_required"].eq("Yes").sum())
    do = int(df["doctorate_required"].eq("Yes").sum())

    def pct(n):
        return f"{(n / total * 100):.0f}% of total" if total else "—"

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-tile">
            <div class="metric-label">Total Postings</div>
            <div class="metric-value">{total}</div>
            <div class="metric-sub">analyzed this session</div>
        </div>
        <div class="metric-tile tile-success">
            <div class="metric-label">Health Science Related</div>
            <div class="metric-value">{hs}</div>
            <div class="metric-sub">{pct(hs)}</div>
        </div>
        <div class="metric-tile tile-violet">
            <div class="metric-label">Masters Required</div>
            <div class="metric-value">{ma}</div>
            <div class="metric-sub">{pct(ma)}</div>
        </div>
        <div class="metric-tile tile-warn">
            <div class="metric-label">Doctorate Required</div>
            <div class="metric-value">{do}</div>
            <div class="metric-sub">{pct(do)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Tabs: Cards / Table / Export ---
    tab_cards, tab_table, tab_export = st.tabs(["Cards", "Table", "Export"])

    # ---------- Cards ----------
    with tab_cards:
        # Filter bar — search + 4 classification filters, each clearly labelled.
        query = st.text_input(
            "Search",
            placeholder="Filter by title, employer, location, or ID...",
            key="filter_q",
        )

        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            hs_filter = st.selectbox(
                "Health Science Related",
                ["All", "Yes", "No"],
                key="filter_hs",
            )
        with fc2:
            ma_filter = st.selectbox(
                "Masters Required",
                ["All", "Yes", "No"],
                key="filter_ma",
            )
        with fc3:
            do_filter = st.selectbox(
                "Doctorate Required",
                ["All", "Yes", "No"],
                key="filter_do",
            )
        with fc4:
            lang_filter = st.selectbox(
                "Language of Work",
                ["All", "English", "French", "Bilingual"],
                key="filter_lang",
            )

        def match(job):
            if query:
                hay = " ".join(str(job.get(k, "")) for k in ("title", "employer", "location", "job_id")).lower()
                if query.lower() not in hay:
                    return False
            if hs_filter != "All" and job.get("health_science_related") != hs_filter:
                return False
            if ma_filter != "All" and job.get("masters_required") != ma_filter:
                return False
            if do_filter != "All" and job.get("doctorate_required") != do_filter:
                return False
            if lang_filter != "All" and (job.get("language_of_work") or "—") != lang_filter:
                return False
            return True

        filtered = [j for j in results if match(j)]

        if not filtered:
            st.markdown("""
                <div class="empty-state">
                    <div class="title">No postings match your filters</div>
                    <div class="desc">Adjust the search or filter criteria above.</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.caption(f"Showing **{len(filtered)}** of **{len(results)}** postings")

            def pill(val, label):
                cls = "pill-yes" if val == "Yes" else "pill-no"
                return f'<span class="pill {cls}">{label}: {val or "-"}</span>'

            for job in filtered:
                title = job.get("title", "Unknown")
                job_id = job.get("job_id", "")
                lang = job.get("language_of_work", "—")

                hs_val = job.get("health_science_related")
                ma_val = job.get("masters_required")
                do_val = job.get("doctorate_required")

                header_html = (
                    f'<span style="font-weight:600; color:#f1f5f9;">{title}</span>'
                    + (f' <code class="mono" style="color:#7dd3fc; font-size:11px;">#{job_id}</code>' if job_id else '')
                )

                with st.expander(f"{title}  ·  #{job_id}" if job_id else title, expanded=True):
                    # Top classification strip
                    strip = (
                        f'<div class="pill-strip">'
                        f'{pill(hs_val, "Health Science")}'
                        f'{pill(ma_val, "Masters Req.")}'
                        f'{pill(do_val, "Doctorate Req.")}'
                        f'<span class="pill pill-lang">Language: {lang}</span>'
                        f'</div>'
                    )
                    st.markdown(strip, unsafe_allow_html=True)

                    # Metadata grid
                    url = job.get("url", "")
                    meta = [
                        ("Employer", job.get("employer", "—")),
                        ("Location", job.get("location", "—")),
                        ("Posted", job.get("posted", "—")),
                        ("Deadline", job.get("deadline", "—")),
                        ("Type", job.get("type", "—")),
                        ("Job ID", f'<code class="mono">{job_id or "—"}</code>'),
                    ]
                    meta_html = '<div class="meta-grid">' + "".join(
                        f'<div class="meta-item"><span class="meta-k">{k}</span><span class="meta-v">{v}</span></div>'
                        for k, v in meta
                    ) + '</div>'
                    st.markdown(meta_html, unsafe_allow_html=True)

                    if url:
                        st.markdown(
                            f'<div style="margin-top:14px;"><a href="{url}" target="_blank" '
                            f'style="color:#7dd3fc; font-family:JetBrains Mono, monospace; font-size:12px; text-decoration:none;">'
                            f'Open original posting</a></div>',
                            unsafe_allow_html=True,
                        )

                    # Nested expander — full description
                    description = job.get("description", "") or "_No description available._"
                    with st.expander("Full Job Description", expanded=False):
                        st.markdown(
                            f'<div class="description-block">{description}</div>',
                            unsafe_allow_html=True,
                        )

    # ---------- Table ----------
    with tab_table:
        st.caption("Compact tabular view · click column headers to sort · drag to resize")
        table_df = df.copy()
        display_cols = [c for c in [
            "title", "employer", "location", "job_id",
            "health_science_related", "masters_required", "doctorate_required",
            "language_of_work", "posted", "deadline", "url",
        ] if c in table_df.columns]

        st.dataframe(
            table_df[display_cols],
            width="stretch",
            hide_index=True,
            column_config={
                "title": st.column_config.TextColumn("Title", width="medium"),
                "employer": st.column_config.TextColumn("Employer", width="small"),
                "location": st.column_config.TextColumn("Location", width="small"),
                "job_id": st.column_config.TextColumn("ID", width="small"),
                "health_science_related": st.column_config.TextColumn("Health Sci", width="small"),
                "masters_required": st.column_config.TextColumn("Masters", width="small"),
                "doctorate_required": st.column_config.TextColumn("Doctorate", width="small"),
                "language_of_work": st.column_config.TextColumn("Lang", width="small"),
                "posted": st.column_config.DateColumn("Posted", width="small"),
                "deadline": st.column_config.DateColumn("Deadline", width="small"),
                "url": st.column_config.LinkColumn("URL", display_text="open"),
            },
        )

    # ---------- Export ----------
    with tab_export:
        st.markdown("Download the analyzed dataset in your preferred format.")
        st.markdown("")

        ec1, ec2 = st.columns(2)
        with ec1:
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "job_analysis.csv",
                "text/csv",
                width="stretch",
            )
            st.caption(f"{len(csv.encode('utf-8')) / 1024:.1f} KB - tabular")
        with ec2:
            json_str = json.dumps(results, indent=2)
            st.download_button(
                "Download JSON",
                json_str,
                "job_analysis.json",
                "application/json",
                width="stretch",
            )
            st.caption(f"{len(json_str.encode('utf-8')) / 1024:.1f} KB - nested")

        st.markdown("")
        with st.expander("Preview JSON payload", expanded=False):
            st.code(json_str, language="json")

else:
    # Empty results state
    if st.session_state.pipeline:
        st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="empty-state">
                <div class="title">Ready to analyze</div>
                <div class="desc">Paste one or more Workday job URLs above and click <b>Analyze</b>.</div>
            </div>
        """, unsafe_allow_html=True)
