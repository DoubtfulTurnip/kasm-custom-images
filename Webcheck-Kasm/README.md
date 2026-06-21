# Webcheck — Kasm Workspace

A custom Kasm workspace container running [Web-Check](https://github.com/Lissy93/web-check), a comprehensive OSINT tool for analysing any website.

## Usage

Pull from GitHub Container Registry:

```bash
docker pull ghcr.io/doubtfulturnip/webcheck-kasm:latest
```

Or deploy via the [DoubtfulTurnip Kasm Registry](https://doubtfulturnip.github.io/doubtfulturnip-kasm-registry/).

## Building from Source

```bash
cd Webcheck-Kasm
docker build -t webcheck-kasm:latest .
```

## Base Image

Built on `kasmweb/ubuntu-noble-desktop:1.19.0-rolling-daily`

## Attribution and Licensing

- **Web-Check** by Alicia Sykes (Lissy93) — [MIT](https://github.com/Lissy93/web-check/blob/master/LICENSE) — source: https://github.com/Lissy93/web-check
