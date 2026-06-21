# Takajo — Kasm Workspace

A custom Kasm workspace container for Windows event log analysis, combining three tools: [Hayabusa](https://github.com/Yamato-Security/hayabusa) (timeline generation), [Takajō](https://github.com/Yamato-Security/takajo) (post-processing), and [Chainsaw](https://github.com/WithSecureLabs/chainsaw) (Sigma-based threat hunting).

## Usage

Pull from GitHub Container Registry:

```bash
docker pull ghcr.io/doubtfulturnip/takajo-kasm:latest
```

Or deploy via the [DoubtfulTurnip Kasm Registry](https://doubtfulturnip.github.io/doubtfulturnip-kasm-registry/).

## Building from Source

```bash
cd Takajo-Kasm
docker build -t takajo-kasm:latest .
```

## Base Image

Built on `kasmweb/ubuntu-noble-desktop:1.19.0-rolling-daily`

## Components

- **[Hayabusa](https://github.com/Yamato-Security/hayabusa)** — Fast Windows event log timeline generator
- **[Takajō](https://github.com/Yamato-Security/takajo)** — Post-processing and analysis of Hayabusa results
- **[Chainsaw](https://github.com/WithSecureLabs/chainsaw)** — Sigma rule-based threat hunting across event logs

## Attribution and Licensing

- **Hayabusa** by Yamato Security — [AGPL-3.0](https://github.com/Yamato-Security/hayabusa/blob/main/LICENSE) — source: https://github.com/Yamato-Security/hayabusa
- **Takajō** by Yamato Security — [AGPL-3.0](https://github.com/Yamato-Security/takajo/blob/main/LICENSE) — source: https://github.com/Yamato-Security/takajo
- **Chainsaw** by WithSecure Labs — [GPL-3.0](https://github.com/WithSecureLabs/chainsaw/blob/master/LICENSE) — source: https://github.com/WithSecureLabs/chainsaw
