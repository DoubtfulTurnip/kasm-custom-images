# Trufflehog WebUI - Kasm Workspace

A custom Kasm workspace container featuring a Streamlit-based web interface for [Trufflehog](https://github.com/trufflesecurity/trufflehog), a powerful secret scanning tool.

## Features

- **Interactive Web Interface** - User-friendly Streamlit UI for running Trufflehog scans
- **Multiple Scan Types** - Support for GitHub, GitLab, filesystem, Docker, S3, and more
- **Advanced Filtering** - Filter results by verification status, detector type, and source
- **Scan History** - Persistent scan history across sessions
- **Expandable Results** - Clean, organized display with detailed expandable entries
- **Verification Explanations** - Built-in tooltips explaining verified vs unverified secrets
- **Dark Theme** - Optimized dark theme for comfortable viewing

## Supported Scan Types

- GitHub Organization
- GitHub Repository
- GitLab
- Filesystem
- Git Repository (URL)
- Docker Image
- S3 Bucket
- Website Crawling
- Postman
- Syslog
- Confluence
- And more...

## Usage

1. Pull the Docker image:
   ```bash
   docker pull bukshee/trufflehog-kasm:1.17.0
   ```

2. Deploy via Kasm Workspaces or run standalone:
   ```bash
   docker run -d -p 6901:6901 bukshee/trufflehog-kasm:1.17.0
   ```

3. Access the workspace and launch the Trufflehog WebUI from the desktop

## Configuration

The WebUI includes configurable options for:
- Verification level (verified, unverified, unknown)
- Custom detector filters
- Results pagination (10, 25, 50, 100, 200 per page)
- Scan history management

## Building from Source

```bash
cd Trufflehog-Kasm
docker build -t trufflehog-kasm:1.17.0 .
```

## Base Image

Built on `kasmweb/ubuntu-noble-desktop:1.17.0`

## Components

- **Trufflehog** - Latest version from trufflesecurity/trufflehog
- **Python 3** - For Streamlit web interface
- **Streamlit** - Web framework for the UI
- **Custom Startup Script** - Automated launch configuration

## License

This container integrates open-source tools. Please refer to individual tool licenses:
- Trufflehog: [AGPL-3.0](https://github.com/trufflesecurity/trufflehog/blob/main/LICENSE)
