# Epagneul — Kasm Workspace

A custom Kasm workspace container running [Epagneul](https://github.com/jurelou/epagneul) for Windows event log visualisation and analysis.

## Usage

Pull from GitHub Container Registry:

```bash
docker pull ghcr.io/doubtfulturnip/epagneul-kasm:latest
```

Or deploy via the [DoubtfulTurnip Kasm Registry](https://doubtfulturnip.github.io/doubtfulturnip-kasm-registry/).

## Building from Source

```bash
cd Epagneul-Kasm
docker build -t epagneul-kasm:latest .
```

## Base Image

Built on `kasmweb/ubuntu-noble-dind:1.19.0-rolling-daily`

## Attribution and Licensing

- **Epagneul** by jurelou — source: https://github.com/jurelou/epagneul — Note: Epagneul does not currently carry a license in its repository.
