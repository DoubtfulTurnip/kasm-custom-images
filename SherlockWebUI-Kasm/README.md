# SherlockWebUI — Kasm Workspace

A custom Kasm workspace container featuring a Streamlit-based web interface for [Sherlock](https://github.com/sherlock-project/sherlock), a tool for hunting down social media accounts by username across social networks.

## Usage

Pull from GitHub Container Registry:

```bash
docker pull ghcr.io/doubtfulturnip/sherlockwebui-kasm:latest
```

Or deploy via the [DoubtfulTurnip Kasm Registry](https://doubtfulturnip.github.io/doubtfulturnip-kasm-registry/).

## Building from Source

```bash
cd SherlockWebUI-Kasm
docker build -t sherlockwebui-kasm:latest .
```

## Base Image

Built on `kasmweb/ubuntu-noble-desktop:1.19.0-rolling-daily`

## Attribution and Licensing

- **Sherlock** by the Sherlock Project — [MIT](https://github.com/sherlock-project/sherlock/blob/master/LICENSE) — source: https://github.com/sherlock-project/sherlock
- **Streamlit** — [Apache-2.0](https://github.com/streamlit/streamlit/blob/develop/LICENSE)

The custom Streamlit UI and startup scripts in this repository are the original work of [DoubtfulTurnip](https://github.com/DoubtfulTurnip).
