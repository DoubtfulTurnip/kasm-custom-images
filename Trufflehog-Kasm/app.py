import json
import os
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
import streamlit as st
import tldextract
from bs4 import BeautifulSoup

# Page configuration
st.set_page_config(
    page_title="Trufflehog WebUI", layout="wide", page_icon="trufflehog-icon.png"
)

# History file path
HISTORY_FILE = os.path.expanduser("~/trufflehog_scan_history.json")


# Load scan history from file
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []


# Save scan history to file
def save_history_to_file(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except:
        pass


# Initialize session state for scan history
if "scan_history" not in st.session_state:
    st.session_state.scan_history = load_history()
if "current_results" not in st.session_state:
    st.session_state.current_results = None

# Apply a purpose-built TruffleHog console theme.
st.markdown(
    """
    <style>
    :root {
        --th-bg: #0b1020;
        --th-panel: #111827;
        --th-panel-2: #172033;
        --th-border: rgba(148, 163, 184, 0.22);
        --th-text: #e5e7eb;
        --th-muted: #94a3b8;
        --th-accent: #f97316;
        --th-accent-2: #22d3ee;
        --th-success: #22c55e;
        --th-warning: #f59e0b;
        --th-danger: #ef4444;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 12% 8%, rgba(249, 115, 22, 0.18), transparent 28rem),
            radial-gradient(circle at 88% 0%, rgba(34, 211, 238, 0.14), transparent 24rem),
            linear-gradient(180deg, #0b1020 0%, #0f172a 48%, #111827 100%) !important;
        color: var(--th-text) !important;
    }

    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.96) !important;
        border-right: 1px solid var(--th-border);
    }

    [data-testid="stSidebar"] *,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] h1,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3 {
        color: var(--th-text) !important;
    }

    .block-container {
        padding-top: 1.5rem;
        max-width: 1380px;
    }

    .hero-card,
    .metric-card,
    .guide-card {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.94), rgba(30, 41, 59, 0.82));
        border: 1px solid var(--th-border);
        border-radius: 22px;
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
    }

    .hero-card {
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.4rem;
    }

    .hero-eyebrow {
        color: var(--th-accent-2) !important;
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    .hero-title {
        color: #ffffff !important;
        font-size: 2.55rem;
        font-weight: 850;
        line-height: 1.04;
        margin: 0.3rem 0 0.45rem;
    }

    .hero-subtitle {
        color: var(--th-muted) !important;
        font-size: 1.02rem;
        line-height: 1.6;
        max-width: 820px;
    }

    .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1rem;
    }

    .th-badge {
        background: rgba(249, 115, 22, 0.12);
        border: 1px solid rgba(249, 115, 22, 0.34);
        border-radius: 999px;
        color: #fed7aa !important;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 0.35rem 0.7rem;
    }

    .metric-card {
        padding: 1rem 1.1rem;
        min-height: 7rem;
    }

    .metric-label {
        color: var(--th-muted) !important;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .metric-value {
        color: #ffffff !important;
        font-size: 2rem;
        font-weight: 850;
        margin-top: 0.3rem;
    }

    .metric-help {
        color: var(--th-muted) !important;
        font-size: 0.85rem;
        margin-top: 0.2rem;
    }

    .guide-card {
        padding: 1rem 1.1rem;
        margin: 0.75rem 0 1.2rem;
    }

    .guide-card strong {
        color: #ffffff !important;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 12px !important;
        border: 1px solid rgba(249, 115, 22, 0.45) !important;
        background: linear-gradient(135deg, #f97316, #ea580c) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        min-height: 2.75rem;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        border-color: rgba(251, 146, 60, 0.9) !important;
        filter: brightness(1.06);
    }

    input, textarea, div[data-baseweb="select"] > div {
        background: rgba(15, 23, 42, 0.96) !important;
        border-color: var(--th-border) !important;
        color: var(--th-text) !important;
        border-radius: 12px !important;
    }

    div[data-testid="stExpander"],
    [data-testid="stDataFrame"] {
        background: rgba(17, 24, 39, 0.82) !important;
        border: 1px solid var(--th-border) !important;
        border-radius: 16px !important;
    }

    code, pre {
        white-space: pre-wrap !important;
        overflow-wrap: anywhere !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_hero():
    st.markdown(
        """
        <div class="hero-card">
          <div class="hero-eyebrow">Secrets discovery workstation</div>
          <div class="hero-title">TruffleHog WebUI</div>
          <div class="hero-subtitle">
            Launch guided scans, review verified and unknown findings, and export evidence
            from a focused Kasm desktop interface. Results are saved locally in Downloads
            as JSONL and can be re-opened from scan history.
          </div>
          <div class="badge-row">
            <span class="th-badge">Verified + unknown findings</span>
            <span class="th-badge">Repository, cloud, web, and filesystem scans</span>
            <span class="th-badge">Local exports</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label, value, help_text):
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


render_hero()

st.sidebar.image("trufflehog-icon.png", width=72)
st.sidebar.markdown("## TruffleHog")
st.sidebar.caption(
    "Choose a scan profile, tune execution, then export the findings you need."
)

# Sidebar: Advanced Settings
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Scan controls")
st.sidebar.info(
    "Run scans only against assets you own or are explicitly authorized to test."
)

# Concurrency control
concurrency = st.sidebar.slider(
    "Concurrency (parallel workers):",
    1,
    20,
    8,
    help="Number of concurrent workers for scanning. Higher = faster but more resource intensive.",
)

# Git clone timeout
git_clone_timeout = st.sidebar.number_input(
    "Git Clone Timeout (seconds):",
    0,
    3600,
    0,
    help="Timeout for git clone operations. 0 = no timeout. Useful for slow/large repositories.",
)

# Detector selection
st.sidebar.markdown("### 🔍 Detector Selection")
enable_all_detectors = st.sidebar.checkbox(
    "Enable All Detectors",
    value=True,
    help="When unchecked, you can select specific detector types",
)

detector_types = []
if not enable_all_detectors:
    st.sidebar.markdown("**Select Detector Categories:**")
    if st.sidebar.checkbox("Cloud Providers (AWS, Azure, GCP)", value=True):
        detector_types.append("cloud")
    if st.sidebar.checkbox("Version Control (GitHub, GitLab)", value=True):
        detector_types.append("vcs")
    if st.sidebar.checkbox("Databases (MongoDB, MySQL, PostgreSQL)", value=True):
        detector_types.append("database")
    if st.sidebar.checkbox("API Keys & Tokens", value=True):
        detector_types.append("api")
    if st.sidebar.checkbox("Private Keys & Certificates", value=True):
        detector_types.append("crypto")

# Scan mode selection
st.sidebar.markdown("---")
desc = {
    "Website Scan": "Scan a web page (single), crawl site, or brute-force directories.",
    "Git Repository Scan": "Scan a remote Git repository.",
    "Local Git Repo Scan": "Scan a local Git repository via file:// URI.",
    "GitHub Org Scan": "Scan all repositories in a GitHub organization.",
    "GitHub Repo + Issues/PR Scan": "Scan issue & PR comments on a GitHub repo.",
    "GitHub Experimental Scan": "Experimental scan over hidden commits.",
    "S3 Bucket Scan": "Scan an AWS S3 bucket for secrets.",
    "S3 Bucket with IAM Role": "Scan S3 using an IAM role ARN.",
    "GCS Bucket Scan": "Scan a Google Cloud Storage bucket.",
    "SSH Git Repo Scan": "Scan a repository over SSH.",
    "Filesystem Scan": "Scan local files or directories.",
    "Postman Workspace Scan": "Scan a Postman workspace or collection.",
    "Jenkins Scan": "Scan a Jenkins server.",
    "ElasticSearch Scan": "Scan an Elasticsearch cluster.",
    "HuggingFace Scan": "Scan HuggingFace models, datasets, and spaces.",
}
scan_mode = st.sidebar.selectbox("Scan Mode:", list(desc.keys()))
st.sidebar.markdown(f"**Description:** {desc[scan_mode]}")

# Scan History in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📜 Scan History")
if st.session_state.scan_history:
    for i, scan in enumerate(
        reversed(st.session_state.scan_history[-10:])
    ):  # Show last 10
        if st.sidebar.button(
            f"{scan['timestamp']} - {scan['mode']} ({scan['count']} results)",
            key=f"history_{i}",
        ):
            st.session_state.current_results = scan["results"]
            st.rerun()
    if st.sidebar.button("Clear History"):
        st.session_state.scan_history = []
        save_history_to_file([])
        st.session_state.current_results = None
        st.rerun()
else:
    st.sidebar.caption("Completed scans will appear here for quick review.")

st.markdown(
    """
    <div class="guide-card">
      <strong>Recommended workflow:</strong> pick the narrowest scan mode, start with verified + unknown results,
      export the raw JSONL evidence from Downloads, and rotate any exposed credentials before sharing findings.
    </div>
    """,
    unsafe_allow_html=True,
)


# Helper function to add common flags to command
def add_common_flags(cmd):
    """Add common Trufflehog flags to command"""
    cmd.extend(["--results=verified,unknown", "--json", "--no-update"])
    if concurrency != 8:  # Only add if not default
        cmd.extend(["--concurrency", str(concurrency)])
    if git_clone_timeout > 0:
        cmd.extend(["--git-clone-timeout", f"{git_clone_timeout}s"])
    return cmd


# Unified TruffleHog runner with progress tracking
def run_trufflehog(cmd, out_file_path=None, show_progress=True):
    records = []
    if out_file_path:
        os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
        mode = "a" if os.path.exists(out_file_path) else "w"
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()

        with open(out_file_path, mode) as out_f:
            line_count = 0
            for line in proc.stdout:
                out_f.write(line)
                out_f.flush()
                try:
                    record = json.loads(line)
                    records.append(record)
                    line_count += 1
                    if show_progress and line_count % 10 == 0:
                        status_text.text(f"Found {line_count} secrets so far...")
                except:
                    continue

        if show_progress:
            progress_bar.progress(100)
            status_text.text(f"Scan complete! Found {line_count} secrets.")

        stderr = proc.stderr.read()
        proc.wait()
        if proc.returncode != 0:
            st.error(f"TruffleHog error: {stderr.strip()}")
        return records
    else:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if proc.returncode != 0:
            st.error(f"TruffleHog error: {proc.stderr.strip()}")
            return []
        for line in proc.stdout.splitlines():
            try:
                records.append(json.loads(line))
            except:
                continue
        return records


# Crawl-and-scan helper with progress tracking
def crawl_and_scan(start_url, max_pages, scope, out_file_path):
    seen, queue, all_results = set(), [start_url], []
    parsed = urlparse(start_url)
    host = parsed.netloc.split(":")[0]
    parts = host.split(".")
    root_domain = ".".join(parts[-2:]) if len(parts) >= 2 else host

    progress_bar = st.progress(0)
    status_text = st.empty()

    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)

        # Update progress
        progress = int((len(seen) / max_pages) * 100)
        progress_bar.progress(progress)
        status_text.text(
            f"Crawling: {len(seen)}/{max_pages} pages | Current: {url[:50]}..."
        )

        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                nl = urlparse(link).netloc.split(":")[0]
                if (
                    scope == "Root Domain"
                    and tldextract.extract(link).registered_domain != root_domain
                ):
                    continue
                if scope == "Exact Host" and nl != host:
                    continue
                if link not in seen:
                    queue.append(link)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
            tmp.write(resp.text.encode())
            tmp.flush()
            cmd = add_common_flags(["trufflehog", "filesystem", tmp.name])
            all_results.extend(run_trufflehog(cmd, out_file_path, show_progress=False))
        except Exception as e:
            st.warning(f"Failed to fetch {url}: {e}")

    progress_bar.progress(100)
    status_text.text(f"Crawl complete! Scanned {len(seen)} pages.")
    return all_results


def mask_secret(value):
    if not value:
        return ""
    if len(value) <= 8:
        return "•" * len(value)
    return f"{value[:4]}{'•' * min(24, len(value) - 8)}{value[-4:]}"


# Function to save scan to history
def save_to_history(scan_mode, records):
    st.session_state.scan_history.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": scan_mode,
            "count": len(records),
            "results": records,
        }
    )
    # Persist to file
    save_history_to_file(st.session_state.scan_history)


# Main logic
records = None

if scan_mode == "Website Scan":
    page_type_descriptions = {
        "Single Page": (
            "Fetches one URL, saves its HTML, and runs TruffleHog's filesystem scanner. "
            "Good for auditing a single page."
        ),
        "Crawl Entire Site": (
            "Starts from the given URL, follows in-domain links up to your max-pages limit, "
            "saving each page's HTML and scanning it."
        ),
        "Directory Brute-Force": (
            "Uses Gobuster with the SecLists raft-small-directories wordlist to discover "
            "common subfolders, then fetches each and scans them with TruffleHog."
        ),
    }
    page_mode = st.radio(
        "Choose Scan Type:", list(page_type_descriptions.keys()), key="page_mode"
    )
    st.markdown(f"**How this works:** {page_type_descriptions[page_mode]}")

    # ────────── Single Page ──────────
    if page_mode == "Single Page":
        url = st.text_input("Enter Website URL:", "https://example.com")
        if st.button("Scan Website"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                f"/home/kasm-user/Desktop/Downloads/trufflehog_single_{ts}.jsonl"
            )
            with st.spinner("Scanning single page..."):
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
                tmp.write(resp.text.encode())
                tmp.flush()
                cmd = add_common_flags(["trufflehog", "filesystem", tmp.name])
                records = run_trufflehog(cmd, output_path)
                save_to_history(scan_mode, records)

    # ────────── Crawl Entire Site ──────────
    elif page_mode == "Crawl Entire Site":
        raw_url = st.text_input(
            "Enter any URL on the site to crawl:", "https://example.com/path"
        )
        max_pages = st.number_input("Max pages to crawl:", 1, 100, 10)
        scope = st.selectbox(
            "Crawl Scope:", ["Root Domain", "Exact Host"], key="crawl_scope"
        )
        scope_desc = {
            "Root Domain": "Follows links whose registered domain matches the site's root (includes subdomains).",
            "Exact Host": "Follows links whose host exactly matches the start URL (no subdomains).",
        }
        st.markdown(f"**Scope explanation:** {scope_desc[scope]}")
        if st.button("Crawl and Scan"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                f"/home/kasm-user/Desktop/Downloads/trufflehog_crawl_{ts}.jsonl"
            )
            parsed = urlparse(raw_url)
            start_site = f"{parsed.scheme}://{parsed.netloc}"
            records = crawl_and_scan(start_site, max_pages, scope, output_path)
            save_to_history(scan_mode, records)

    # ────────── Directory Brute-Force ──────────
    else:
        base_url = st.text_input(
            "Enter base URL (e.g. https://example.com):", "https://example.com"
        )
        threads = st.number_input("Gobuster threads:", 10, 100, 50)
        if st.button("Scan Directories"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                f"/home/kasm-user/Desktop/Downloads/trufflehog_dirbf_{ts}.jsonl"
            )
            gobuster_log_path = os.path.join(
                os.path.dirname(output_path), f"gobuster_dirbf_{ts}.txt"
            )
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Use bundled wordlist; fall back to downloading if missing
            _bundled_wl = "/usr/share/wordlists/raft-small-directories.txt"
            if os.path.exists(_bundled_wl):
                wl_path = _bundled_wl
            else:
                with st.spinner("Downloading wordlist..."):
                    wl_url = (
                        "https://raw.githubusercontent.com/danielmiessler/"
                        "SecLists/master/Discovery/Web-Content/raft-small-directories.txt"
                    )
                    wl_resp = requests.get(wl_url)
                    wl_resp.raise_for_status()
                    tmp_wl = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
                    tmp_wl.write(wl_resp.content)
                    tmp_wl.flush()
                    wl_path = tmp_wl.name

            # Run Gobuster with progress
            with st.spinner("Running Gobuster..."):
                cmd = [
                    "gobuster",
                    "dir",
                    "-u",
                    base_url,
                    "-w",
                    wl_path,
                    "-t",
                    str(threads),
                    "-e",
                    "-s",
                    "200,204,301,302,307,401,403",
                    "-b",
                    "",
                    "-q",
                    "-o",
                    gobuster_log_path,
                ]
                st.text(f"🔍 Running command: {' '.join(cmd)}")
                subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                st.text(f"📄 Gobuster log saved to: {gobuster_log_path}")

            # Parse found URLs
            found_paths = []
            with open(gobuster_log_path) as gf:
                for line in gf:
                    line = line.strip()
                    if not line or line.startswith("===="):
                        continue
                    url_candidate = line.split()[0]
                    found_paths.append(url_candidate)
            st.success(f"Found {len(found_paths)} paths")

            # Fetch each and scan with progress
            records = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, full_url in enumerate(found_paths):
                progress = int(((idx + 1) / len(found_paths)) * 100)
                progress_bar.progress(progress)
                status_text.text(f"Scanning {idx + 1}/{len(found_paths)}: {full_url}")

                try:
                    resp = requests.get(full_url, timeout=10)
                    resp.raise_for_status()
                    tmp_html = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
                    tmp_html.write(resp.text.encode())
                    tmp_html.flush()
                    cmd = add_common_flags(["trufflehog", "filesystem", tmp_html.name])
                    records.extend(
                        run_trufflehog(cmd, output_path, show_progress=False)
                    )
                except Exception as e:
                    st.warning(f"Failed to fetch {full_url}: {e}")

            progress_bar.progress(100)
            status_text.text(f"Directory scan complete!")
            save_to_history(scan_mode, records)

elif scan_mode == "Git Repository Scan":
    repo = st.text_input("Enter Git Repo URL:", "https://github.com/user/repo.git")
    if st.button("Scan Repository"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_gitrepo_{ts}.jsonl"
        with st.spinner("Scanning repository..."):
            cmd = add_common_flags(["trufflehog", "git", repo])
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "Local Git Repo Scan":
    path = st.text_input("Enter Local Path:", "file://./repo")
    if st.button("Scan Local Repo"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = (
            f"/home/kasm-user/Desktop/Downloads/trufflehog_localgit_{ts}.jsonl"
        )
        with st.spinner("Scanning local repo..."):
            cmd = add_common_flags(["trufflehog", "git", path])
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "GitHub Org Scan":
    org = st.text_input("Enter GitHub Org:", "trufflesecurity")
    if st.button("Scan Org"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = (
            f"/home/kasm-user/Desktop/Downloads/trufflehog_githuborg_{ts}.jsonl"
        )
        with st.spinner("Scanning org..."):
            cmd = add_common_flags(["trufflehog", "github", "--org", org])
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "GitHub Repo + Issues/PR Scan":
    repo = st.text_input("Enter GitHub Repo URL:", "https://github.com/user/repo.git")
    if st.button("Scan Issues/PRs"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = (
            f"/home/kasm-user/Desktop/Downloads/trufflehog_ghissues_{ts}.jsonl"
        )
        with st.spinner("Scanning issue/PR comments..."):
            cmd = add_common_flags(
                [
                    "trufflehog",
                    "github",
                    "--repo",
                    repo,
                    "--issue-comments",
                    "--pr-comments",
                ]
            )
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "GitHub Experimental Scan":
    repo = st.text_input("Enter Repo URL:", "https://github.com/user/repo.git")
    if st.button("Run Experimental Scan"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_ghexp_{ts}.jsonl"
        with st.spinner("Running experimental scan..."):
            cmd = add_common_flags(
                [
                    "trufflehog",
                    "github-experimental",
                    "--repo",
                    repo,
                    "--object-discovery",
                    "--delete-cached-data",
                ]
            )
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "S3 Bucket Scan":
    bucket = st.text_input("Enter S3 Bucket:", "my-bucket")
    if st.button("Scan S3 Bucket"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_s3_{ts}.jsonl"
        with st.spinner("Scanning S3 bucket..."):
            cmd = add_common_flags(["trufflehog", "s3", "--bucket", bucket])
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "S3 Bucket with IAM Role":
    role = st.text_input("Enter IAM Role ARN:", "arn:aws:iam::123456789012:role/MyRole")
    if st.button("Scan S3 with Role"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_s3role_{ts}.jsonl"
        with st.spinner("Scanning S3 with IAM role..."):
            cmd = add_common_flags(["trufflehog", "s3", "--role-arn", role])
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "GCS Bucket Scan":
    pid = st.text_input("Enter GCP Project ID:", "my-project")
    if st.button("Scan GCS Bucket"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_gcs_{ts}.jsonl"
        with st.spinner("Scanning GCS bucket..."):
            cmd = add_common_flags(
                ["trufflehog", "gcs", "--project-id", pid, "--cloud-environment"]
            )
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "SSH Git Repo Scan":
    ssh_url = st.text_input("Enter SSH Git URL:", "git@github.com:user/repo.git")
    if st.button("Scan SSH Repo"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_ssh_{ts}.jsonl"
        with st.spinner("Scanning SSH repo..."):
            cmd = add_common_flags(["trufflehog", "git", ssh_url])
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "Filesystem Scan":
    paths = st.text_input("Enter paths comma-separated:", "/file1.txt,/dir")
    if st.button("Scan Filesystem"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_fs_{ts}.jsonl"
        with st.spinner("Scanning filesystem..."):
            items = [p.strip() for p in paths.split(",")]
            cmd = add_common_flags(["trufflehog", "filesystem"] + items)
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "Postman Workspace Scan":
    token = st.text_input("Postman API Token:", "")
    ws = st.text_input("Workspace ID:", "")
    coll = st.text_input("Collection ID:", "")
    if st.button("Scan Postman Workspace"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_postman_{ts}.jsonl"
        with st.spinner("Scanning Postman workspace..."):
            cmd = add_common_flags(
                [
                    "trufflehog",
                    "postman",
                    "--token",
                    token,
                    "--workspace-id",
                    ws,
                    "--collection-id",
                    coll,
                ]
            )
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "Jenkins Scan":
    url = st.text_input("Jenkins URL:", "https://jenkins.example.com")
    user = st.text_input("Username:", "admin")
    pwd = st.text_input("Password:", "", type="password")
    if st.button("Scan Jenkins Server"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_jenkins_{ts}.jsonl"
        with st.spinner("Scanning Jenkins server..."):
            cmd = add_common_flags(
                [
                    "trufflehog",
                    "jenkins",
                    "--url",
                    url,
                    "--username",
                    user,
                    "--password",
                    pwd,
                ]
            )
            records = run_trufflehog(cmd, output_path)
            save_to_history(scan_mode, records)

elif scan_mode == "ElasticSearch Scan":
    nodes = st.text_input("Elasticsearch nodes comma-separated:", "127.0.0.1:9200")
    auth_type = st.selectbox(
        "Auth type:", ["username_password", "service_token", "cloud_id_api_key"]
    )
    args = ["trufflehog", "elasticsearch"] + nodes.split(",")
    if auth_type == "username_password":
        u = st.text_input("User:", "")
        p = st.text_input("Password:", "", type="password")
        args += ["--username", u, "--password", p]
    elif auth_type == "service_token":
        tkn = st.text_input("Service token:", "")
        args += ["--service-token", tkn]
    else:
        cid = st.text_input("Cloud ID:", "")
        ak = st.text_input("API Key:", "")
        args += ["--cloud-id", cid, "--api-key", ak]
    if st.button("Scan Elasticsearch"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_es_{ts}.jsonl"
        cmd = add_common_flags(args)
        records = run_trufflehog(cmd, output_path)
        save_to_history(scan_mode, records)

elif scan_mode == "HuggingFace Scan":
    model = st.text_input("Model ID:", "")
    space = st.text_input("Space ID:", "")
    dset = st.text_input("Dataset ID:", "")
    org = st.text_input("Organization/User:", "")
    incl = st.checkbox("Include discussions/PRs")
    if st.button("Scan HuggingFace"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/home/kasm-user/Desktop/Downloads/trufflehog_hf_{ts}.jsonl"
        args = ["trufflehog", "huggingface"]
        if model:
            args += ["--model", model]
        if space:
            args += ["--space", space]
        if dset:
            args += ["--dataset", dset]
        if org:
            args += ["--org", org]
        if incl:
            args += ["--include-discussions", "--include-prs"]
        cmd = add_common_flags(args)
        records = run_trufflehog(cmd, output_path)
        save_to_history(scan_mode, records)

# Store new scan results in session state
if records is not None:
    st.session_state.current_results = records

# Always use results from session state for display (persists across reruns)
if st.session_state.current_results is not None:
    records = st.session_state.current_results

# Display results with filtering
if records is not None:
    if not records:
        st.success("✅ No secrets found.")
    else:
        verified_count = sum(1 for r in records if r.get("Verified", False))
        unknown_count = len(records) - verified_count
        detector_count = len(set(r.get("DetectorName", "Unknown") for r in records))

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            render_metric_card(
                "Total findings", len(records), "All findings returned by TruffleHog"
            )
        with metric_col2:
            render_metric_card(
                "Verified secrets", verified_count, "Confirmed active credentials"
            )
        with metric_col3:
            render_metric_card(
                "Detector types", detector_count, "Unique detectors represented"
            )

        if verified_count:
            st.error(
                f"{verified_count} verified secret(s) require immediate triage and credential rotation."
            )
        elif unknown_count:
            st.warning(
                f"{unknown_count} unknown finding(s) need validation before closing the scan."
            )

        # Result filtering
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_verified = st.multiselect(
                "Filter by Verification:",
                ["Verified", "Unverified"],
                default=["Verified", "Unverified"],
            )

        with col2:
            detector_names = sorted(
                list(set(r.get("DetectorName", "Unknown") for r in records))
            )
            filter_detector = st.multiselect(
                "Filter by Detector:",
                options=detector_names,
                default=detector_names,  # All selected by default
                help="Select one or more detector types to filter results",
            )

        with col3:
            reveal_secrets = st.checkbox(
                "Reveal secret values",
                value=False,
                help="Keep disabled for screenshots or demos. Exports still contain raw values.",
            )
            st.markdown("**Export Results:**")
            export_col1, export_col2 = st.columns(2)

        # Apply filters
        filtered_records = records

        # Filter by verification status
        if len(filter_verified) > 0 and len(filter_verified) < 2:
            # Only one option selected
            if "Verified" in filter_verified:
                filtered_records = [
                    r for r in filtered_records if r.get("Verified", False)
                ]
            else:  # Only "Unverified" selected
                filtered_records = [
                    r for r in filtered_records if not r.get("Verified", False)
                ]
        # If both or neither selected, show all records

        # Filter by detector type
        if len(filter_detector) > 0:
            filtered_records = [
                r
                for r in filtered_records
                if r.get("DetectorName", "Unknown") in filter_detector
            ]

        # Reset to page 1 if filters changed
        if "last_filter_state" not in st.session_state:
            st.session_state.last_filter_state = (filter_verified, filter_detector)

        current_filter_state = (tuple(filter_verified), tuple(filter_detector))
        if st.session_state.last_filter_state != current_filter_state:
            st.session_state.page_number = 1
            st.session_state.last_filter_state = current_filter_state

        # Pagination settings
        results_per_page = st.selectbox(
            "Results per page:",
            options=[10, 25, 50, 100, 200],
            index=2,  # Default to 50
            help="Select how many results to display per page",
        )

        total_results = len(filtered_records)
        total_pages = (total_results + results_per_page - 1) // results_per_page

        # Initialize page number in session state
        if "page_number" not in st.session_state:
            st.session_state.page_number = 1

        st.subheader(
            f"Scan Results (Showing {len(filtered_records)} of {len(records)})"
        )

        # Add verification status explanation
        with st.expander("ℹ️ Understanding Results", expanded=False):
            st.markdown("""
            **Verification Status:**
            - **VERIFIED ✅** - The secret was tested and confirmed to be valid/active. This is a real, working credential.
            - **Unverified ⚠️** - The secret was detected but not verified. It may be valid, expired, or a false positive.

            **Detector** - The type of secret found (e.g., AWS, GitHub, API Key)

            **Source** - Where the secret was found (e.g., file path, repository, URL)
            """)

        # Create summary dataframe for current page
        start_idx = (st.session_state.page_number - 1) * results_per_page
        end_idx = min(start_idx + results_per_page, total_results)
        current_page_records = filtered_records[start_idx:end_idx]

        # Display results with expandable details
        for i, r in enumerate(current_page_records, start=start_idx):
            verified = r.get("Verified", False)
            verified_status = "VERIFIED ✅" if verified else "Unverified ⚠️"
            detector = r.get("DetectorName", "Unknown")
            source = r.get("SourceName", "")

            # Create human-readable summary
            summary = (
                f"#{i + 1} — {verified_status} — {detector} secret — Source: {source}"
            )

            with st.expander(summary, expanded=False):
                col1, col2 = st.columns([1, 3])

                with col1:
                    st.markdown("**Details:**")
                    st.write(f"**Detector:** {detector}")
                    st.write(f"**Verified:** {verified_status}")
                    st.write(f"**Source:** {source}")
                    if r.get("SourceType"):
                        st.write(f"**Source Type:** {r.get('SourceType')}")

                with col2:
                    raw_value = r.get("Raw", "")
                    raw_v2_value = r.get("RawV2", "")
                    st.markdown("**Secret Value:**")
                    if reveal_secrets:
                        st.code(raw_value, language="text")
                    else:
                        st.code(mask_secret(raw_value), language="text")
                        st.caption(
                            "Enable 'Reveal secret values' above to view the full value."
                        )

                    if raw_v2_value:
                        st.markdown("**Additional Data:**")
                        st.code(
                            (
                                raw_v2_value
                                if reveal_secrets
                                else mask_secret(raw_v2_value)
                            ),
                            language="text",
                        )

                st.markdown("---")
                st.markdown("**Full JSON Data:**")
                st.json(r)

        # Pagination controls
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⬅️ Previous", disabled=(st.session_state.page_number == 1)):
                st.session_state.page_number -= 1
                st.rerun()
        with col_info:
            st.markdown(
                f"**Page {st.session_state.page_number} of {total_pages}** (Showing {start_idx + 1}-{end_idx} of {total_results})"
            )
        with col_next:
            if st.button(
                "Next ➡️", disabled=(st.session_state.page_number >= total_pages)
            ):
                st.session_state.page_number += 1
                st.rerun()

        # Export buttons
        with export_col1:
            data_json = json.dumps(filtered_records, indent=2)
            st.download_button(
                "📥 Download JSON",
                data_json,
                f"trufflehog_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json",
                use_container_width=True,
            )

        with export_col2:
            # Create CSV from filtered records
            csv_rows = [
                {
                    "Verified": "✅" if r.get("Verified") else "❌",
                    "DetectorName": r.get("DetectorName", ""),
                    "SourceName": r.get("SourceName", ""),
                    "SourceType": r.get("SourceType", ""),
                    "Raw": r.get("Raw", ""),
                }
                for r in filtered_records
            ]
            csv_df = pd.DataFrame(csv_rows)
            csv_data = csv_df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv_data,
                f"trufflehog_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True,
            )
