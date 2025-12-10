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
st.set_page_config(page_title="Trufflehog WebUI", layout="wide")

# Initialize session state for scan history
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []
if "current_results" not in st.session_state:
    st.session_state.current_results = None

# Theme selection
theme = st.sidebar.selectbox("Theme:", ["Light", "Dark"], index=1)
if theme == "Dark":
    st.markdown(
        """
        <style>
        /* Main app and sidebar backgrounds */
        [data-testid="stAppViewContainer"] {
            background-color: #0E1117 !important;
            color: #FAFAFA !important;
        }
        [data-testid="stSidebar"] {
            background-color: #1E1E1E !important;
        }

        /* All text elements - force white/light text */
        .stMarkdown, .stText, p, span, div, h1, h2, h3, h4, h5, h6, label,
        .stSelectbox label, .stNumberInput label, .stSlider label,
        .stCheckbox label, .stRadio label, .stTextInput label,
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span, [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] .stMarkdown {
            color: #FAFAFA !important;
        }

        /* Buttons */
        div.stButton > button {
            background-color: #4A4A4A !important;
            color: #FFFFFF !important;
            border: 1px solid #666666 !important;
        }
        div.stButton > button:hover {
            background-color: #5A5A5A !important;
            border-color: #888888 !important;
        }

        /* Download buttons */
        div.stDownloadButton > button {
            background-color: #FF6B35 !important;
            color: #FFFFFF !important;
            border: 1px solid #FF8555 !important;
        }
        div.stDownloadButton > button:hover {
            background-color: #FF7B45 !important;
        }

        /* Input fields */
        input, textarea {
            background-color: #2D2D2D !important;
            color: #FAFAFA !important;
            border: 1px solid #555555 !important;
        }
        input:focus, textarea:focus {
            border-color: #888888 !important;
            box-shadow: 0 0 0 1px #888888 !important;
        }

        /* Select dropdowns */
        select, div[data-baseweb="select"] {
            background-color: #2D2D2D !important;
            color: #FAFAFA !important;
        }
        div[role="option"] {
            background-color: #2D2D2D !important;
            color: #FAFAFA !important;
        }
        div[role="option"]:hover {
            background-color: #3D3D3D !important;
        }

        /* Multiselect tags */
        div[data-baseweb="tag"] {
            background-color: #FF6B35 !important;
            color: #FFFFFF !important;
        }

        /* Placeholders */
        ::placeholder {
            color: #999999 !important;
        }

        /* Dataframes and tables */
        .stDataFrame, table {
            background-color: #1E1E1E !important;
            color: #FAFAFA !important;
        }
        thead tr th {
            background-color: #2D2D2D !important;
            color: #FFFFFF !important;
        }
        tbody tr {
            background-color: #1E1E1E !important;
            color: #FAFAFA !important;
        }
        tbody tr:hover {
            background-color: #2D2D2D !important;
        }

        /* Expanders */
        .streamlit-expanderHeader {
            background-color: #2D2D2D !important;
            color: #FAFAFA !important;
        }
        .streamlit-expanderContent {
            background-color: #1E1E1E !important;
            color: #FAFAFA !important;
        }

        /* Sliders */
        div[data-baseweb="slider"] {
            color: #FAFAFA !important;
        }
        div[data-baseweb="slider"] div {
            color: #FAFAFA !important;
        }

        /* Progress bars */
        .stProgress > div > div {
            background-color: #FF6B35 !important;
        }

        /* Number input increment/decrement buttons */
        button[kind="stepUp"], button[kind="stepDown"] {
            color: #FAFAFA !important;
        }

        /* Help tooltips */
        .stTooltipIcon {
            color: #AAAAAA !important;
        }

        /* Section headers in sidebar */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
            color: #FFFFFF !important;
        }

        /* Success/Error/Warning/Info boxes text should stay readable */
        .stSuccess {
            background-color: #1E7B34 !important;
            color: #FFFFFF !important;
        }
        .stError {
            background-color: #C92A2A !important;
            color: #FFFFFF !important;
        }
        .stWarning {
            background-color: #F76707 !important;
            color: #FFFFFF !important;
        }
        .stInfo {
            background-color: #1971C2 !important;
            color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title("🔍 Trufflehog WebUI")

# Sidebar: Advanced Settings
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Advanced Settings")

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
        st.rerun()
else:
    st.sidebar.text("No scan history yet")


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

            # Download wordlist
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

            # Run Gobuster with progress
            with st.spinner("Running Gobuster..."):
                cmd = [
                    "gobuster",
                    "dir",
                    "-u",
                    base_url,
                    "-w",
                    tmp_wl.name,
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

# Use current_results from session state if available (from history click)
if st.session_state.current_results is not None and records is None:
    records = st.session_state.current_results
    st.session_state.current_results = None  # Clear after using

# Display results with filtering
if records is not None:
    if not records:
        st.success("✅ No secrets found.")
    else:
        # Result filtering
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            filter_verified = st.multiselect(
                "Filter by Verification:",
                ["Verified", "Unverified"],
                default=["Verified", "Unverified"],
            )

        with col2:
            detector_names = list(
                set(r.get("DetectorName", "Unknown") for r in records)
            )
            filter_detector = st.multiselect(
                "Filter by Detector:", ["All"] + detector_names, default=["All"]
            )

        with col3:
            source_names = list(set(r.get("SourceName", "Unknown") for r in records))
            filter_source = st.multiselect(
                "Filter by Source:", ["All"] + source_names, default=["All"]
            )

        with col4:
            st.markdown("**Export Results:**")
            export_col1, export_col2 = st.columns(2)

        # Apply filters
        filtered_records = records
        if "Verified" not in filter_verified:
            filtered_records = [
                r for r in filtered_records if not r.get("Verified", False)
            ]
        if "Unverified" not in filter_verified:
            filtered_records = [r for r in filtered_records if r.get("Verified", False)]
        if "All" not in filter_detector:
            filtered_records = [
                r
                for r in filtered_records
                if r.get("DetectorName", "Unknown") in filter_detector
            ]
        if "All" not in filter_source:
            filtered_records = [
                r
                for r in filtered_records
                if r.get("SourceName", "Unknown") in filter_source
            ]

        st.subheader(
            f"Summary of Results (Showing {len(filtered_records)} of {len(records)})"
        )

        # Create summary dataframe
        rows = [
            {
                "SourceName": r.get("SourceName", ""),
                "DetectorName": r.get("DetectorName", ""),
                "Verified": "✅" if r.get("Verified") else "❌",
                "Raw": (r.get("Raw", "")[:30] + "...") if r.get("Raw") else "",
            }
            for r in filtered_records
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

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
            csv_data = df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv_data,
                f"trufflehog_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True,
            )

        st.subheader("Detailed Records")
        for i, r in enumerate(filtered_records):
            verified_icon = "✅ Verified" if r.get("Verified") else "❌ Unverified"
            with st.expander(
                f"Record {i + 1}: {verified_icon} - {r.get('DetectorName', 'Unknown')} - {r.get('SourceName', '')}"
            ):
                st.json(r)
