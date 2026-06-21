# BloodHound CE — Kasm Workspace

A custom Kasm workspace container running [BloodHound Community Edition](https://github.com/SpecterOps/BloodHound) for Active Directory and Azure attack path analysis.

## Usage

Pull from GitHub Container Registry:

```bash
docker pull ghcr.io/doubtfulturnip/bloodhound-kasm:latest
```

Or deploy via the [DoubtfulTurnip Kasm Registry](https://doubtfulturnip.github.io/doubtfulturnip-kasm-registry/).

## Building from Source

```bash
cd BloodHound-Kasm
docker build -t bloodhound-kasm:latest .
```

## Base Image

Built on `kasmweb/ubuntu-noble-dind:1.19.0-rolling-daily`

## Attribution and Licensing

- **BloodHound Community Edition** by SpecterOps — [Apache-2.0](https://github.com/SpecterOps/BloodHound/blob/main/LICENSE) — source: https://github.com/SpecterOps/BloodHound
