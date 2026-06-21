# TruffleHog WebUI — Kasm Workspace

A custom Kasm workspace container featuring a Streamlit-based web interface for [TruffleHog](https://github.com/trufflesecurity/trufflehog), a secrets scanning tool by Truffle Security.

## Features

- **Interactive Web Interface** — Streamlit UI for running TruffleHog scans without the command line
- **Multiple Scan Types** — GitHub, GitLab, filesystem, Docker, S3, website, Postman, Syslog, Confluence, and more
- **Gobuster Integration** — Directory brute-forcing with bundled SecLists wordlist
- **Advanced Filtering** — Filter results by verification status, detector type, and source
- **Scan History** — Persistent scan history across sessions
- **Dark Theme** — Optimised for comfortable viewing

## Supported Scan Types

- GitHub Organisation / Repository
- GitLab
- Filesystem
- Git Repository (URL)
- Docker Image
- S3 Bucket
- Website Crawling
- Postman
- Syslog
- Confluence

## Usage

Pull from GitHub Container Registry:

```bash
docker pull ghcr.io/doubtfulturnip/trufflehog-kasm:latest
```

Or deploy via the [DoubtfulTurnip Kasm Registry](https://doubtfulturnip.github.io/doubtfulturnip-kasm-registry/).

## Building from Source

```bash
cd Trufflehog-Kasm
docker build -t trufflehog-kasm:latest .
```

## Base Image

Built on `kasmweb/ubuntu-noble-desktop:1.19.0-rolling-daily`

## Components

- **[TruffleHog](https://github.com/trufflesecurity/trufflehog)** — Secrets scanning engine
- **[Gobuster](https://github.com/OJ/gobuster)** — Directory/file brute-forcing
- **[Streamlit](https://streamlit.io)** — Web framework for the custom UI
- **SecLists** — Bundled wordlist for Gobuster scans

## Attribution and Licensing

This workspace packages the following open-source tools. Their licenses apply to the respective components:

- **TruffleHog** by Truffle Security Co. — [AGPL-3.0](https://github.com/trufflesecurity/trufflehog/blob/main/LICENSE) — source: https://github.com/trufflesecurity/trufflehog
- **Gobuster** by OJ Reeves — [Apache-2.0](https://github.com/OJ/gobuster/blob/master/LICENSE)
- **Streamlit** — [Apache-2.0](https://github.com/streamlit/streamlit/blob/develop/LICENSE)
- **SecLists** by Daniel Miessler — [MIT](https://github.com/danielmiessler/SecLists/blob/master/LICENSE)

The custom Streamlit UI and startup scripts in this repository are the original work of [DoubtfulTurnip](https://github.com/DoubtfulTurnip).
