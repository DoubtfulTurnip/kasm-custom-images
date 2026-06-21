# Slasher — Kasm Workspace

A custom Kasm workspace container running [Slasher](https://github.com/hexastrike/slasher), a web application vulnerability scanner.

## Usage

Pull from GitHub Container Registry:

```bash
docker pull ghcr.io/doubtfulturnip/slasher-kasm:latest
```

Or deploy via the [DoubtfulTurnip Kasm Registry](https://doubtfulturnip.github.io/doubtfulturnip-kasm-registry/).

## Building from Source

```bash
cd Slasher-Kasm
docker build -t slasher-kasm:latest .
```

## Base Image

Built on `kasmweb/firefox:1.19.0-rolling-daily`

## Attribution and Licensing

- **Slasher** by hexastrike — [MIT](https://github.com/hexastrike/slasher/blob/main/LICENSE) — source: https://github.com/hexastrike/slasher
