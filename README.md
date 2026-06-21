# Custom Kasm Workspace Images

Custom [Kasm](https://www.kasmweb.com/) workspace containers for open-source cybersecurity tools, automatically rebuilt when upstream projects release new versions.

Images are published to the [GitHub Container Registry](https://github.com/DoubtfulTurnip?tab=packages).

## Adding the Registry

Add the DoubtfulTurnip 3rd party registry to your Kasm instance — see [Kasm's registry documentation](https://kasmweb.com/docs/develop/guide/workspace_registry.html).

Registry URL: `https://doubtfulturnip.github.io/doubtfulturnip-kasm-registry/`

## Workspaces

### [TruffleHog](https://github.com/trufflesecurity/trufflehog)
Secrets scanning tool with a custom Streamlit web interface for running scans without the command line.
Image: `ghcr.io/doubtfulturnip/trufflehog-kasm:latest`
License: [AGPL-3.0](https://github.com/trufflesecurity/trufflehog/blob/main/LICENSE)

---

### [SherlockWebUI](https://github.com/sherlock-project/sherlock)
Hunt down social media accounts by username across social networks, wrapped in a Streamlit web interface.
Image: `ghcr.io/doubtfulturnip/sherlockwebui-kasm:latest`
License: [MIT](https://github.com/sherlock-project/sherlock/blob/master/LICENSE)

---

### [SocialAnalyzer](https://github.com/qeeqbox/social-analyzer)
API, CLI and web application for analysing and finding a person's profile across social media.
Image: `ghcr.io/doubtfulturnip/socialanalyzer-kasm:latest`
License: [AGPL-3.0](https://github.com/qeeqbox/social-analyzer/blob/main/LICENSE)

---

### [Takajo](https://github.com/Yamato-Security/takajo)
EVTX analysis workspace combining Hayabusa (timeline generation), Takajō (post-processing), and Chainsaw (Sigma-based threat hunting).

- [Hayabusa](https://github.com/Yamato-Security/hayabusa) — [AGPL-3.0](https://github.com/Yamato-Security/hayabusa/blob/main/LICENSE)
- [Takajō](https://github.com/Yamato-Security/takajo) — [AGPL-3.0](https://github.com/Yamato-Security/takajo/blob/main/LICENSE)
- [Chainsaw](https://github.com/WithSecureLabs/chainsaw) — [GPL-3.0](https://github.com/WithSecureLabs/chainsaw/blob/master/LICENSE)

Image: `ghcr.io/doubtfulturnip/takajo-kasm:latest`

---

### [Webcheck](https://github.com/Lissy93/web-check)
Comprehensive OSINT tool for analysing any website.
Image: `ghcr.io/doubtfulturnip/webcheck-kasm:latest`
License: [MIT](https://github.com/Lissy93/web-check/blob/master/LICENSE)

---

### [BloodHound CE](https://github.com/SpecterOps/BloodHound)
Active Directory and Azure attack path analysis tool.
Image: `ghcr.io/doubtfulturnip/bloodhound-kasm:latest`
License: [Apache-2.0](https://github.com/SpecterOps/BloodHound/blob/main/LICENSE)

---

### [Epagneul](https://github.com/jurelou/epagneul)
Windows event log visualisation and analysis tool.
Image: `ghcr.io/doubtfulturnip/epagneul-kasm:latest`
Note: Epagneul does not currently carry a license in its repository.

---

### [Slasher](https://github.com/hexastrike/slasher)
Web application vulnerability scanner.
Image: `ghcr.io/doubtfulturnip/slasher-kasm:latest`
License: [MIT](https://github.com/hexastrike/slasher/blob/main/LICENSE)

---

## Building from Source

```bash
docker build -t <image-name>:latest ./<Workspace-Dir>
```

See [Kasm's custom image documentation](https://www.kasmweb.com/docs/latest/how_to/building_images.html) for deployment instructions.
