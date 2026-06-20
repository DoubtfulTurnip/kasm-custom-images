FROM kasmweb/ubuntu-noble-dind:1.19.0-rolling-daily

USER root

ARG SOCIAL_ANALYZER_COMMIT=1ba0905e00d054aab833eb3693739c354db09e0f
ARG SOCIAL_ANALYZER_APP_IMAGE=ghcr.io/doubtfulturnip/socialanalyzer-app:latest
LABEL org.opencontainers.image.source="https://github.com/qeeqbox/social-analyzer" \
      org.opencontainers.image.revision="${SOCIAL_ANALYZER_COMMIT}"

ENV HOME       /home/kasm-user
ENV STARTUPDIR /dockerstartup
WORKDIR $HOME

# Install curl, notifications, and the Docker Compose plugin.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libnotify-bin \
    docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

# Runtime startup should only pull and run the prebuilt GHCR app image.
RUN mkdir -p /opt/social-analyzer && \
    printf '%s\n' "${SOCIAL_ANALYZER_COMMIT}" > /opt/social-analyzer.UPSTREAM_COMMIT && \
    printf '%s\n' \
      'services:' \
      '  social-analyzer:' \
      "    image: ${SOCIAL_ANALYZER_APP_IMAGE}" \
      '    ports:' \
      '      - "9005:9005"' \
      '    environment:' \
      '      PORT: "9005"' \
      '    shm_size: "2gb"' \
      '    restart: unless-stopped' \
      '    healthcheck:' \
      '      test: ["CMD-SHELL", "wget -q -O /dev/null http://localhost:9005/app.html"]' \
      '      interval: 10s' \
      '      timeout: 5s' \
      '      retries: 30' \
      > /opt/social-analyzer/docker-compose.yml && \
    chown -R 1000:0 /opt/social-analyzer /opt/social-analyzer.UPSTREAM_COMMIT

# Copy in our custom startup script and rename it to custom_startup.sh.
COPY custom_startup_socialanalyzer.sh $STARTUPDIR/custom_startup.sh
RUN chmod +x $STARTUPDIR/custom_startup.sh && \
    chown 1000:0 $STARTUPDIR/custom_startup.sh

# Switch to non-root for execution.
USER 1000
WORKDIR $HOME