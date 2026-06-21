# SocialAnalyzer — Kasm Workspace

A custom Kasm workspace container running [SocialAnalyzer](https://github.com/qeeqbox/social-analyzer) for analysing and finding a person's profile across social media platforms.

## Build Architecture

This workspace uses a dual-image build pattern:

- `app.Dockerfile` — builds the SocialAnalyzer application image (pushed to GHCR as `socialanalyzer-app`)
- `Dockerfile` — builds the Kasm workspace that pulls in the prebuilt app image at startup via Docker Compose

## Usage

Pull from GitHub Container Registry:

```bash
docker pull ghcr.io/doubtfulturnip/socialanalyzer-kasm:latest
```

Or deploy via the [DoubtfulTurnip Kasm Registry](https://doubtfulturnip.github.io/doubtfulturnip-kasm-registry/).

## Building from Source

```bash
cd SocialAnalyzer-Kasm
docker build -t socialanalyzer-kasm:latest .
```

## Base Image

Built on `kasmweb/ubuntu-noble-dind:1.19.0-rolling-daily`

## Attribution and Licensing

- **SocialAnalyzer** by qeeqbox — [AGPL-3.0](https://github.com/qeeqbox/social-analyzer/blob/main/LICENSE) — source: https://github.com/qeeqbox/social-analyzer
