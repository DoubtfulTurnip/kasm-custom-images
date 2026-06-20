FROM kasmweb/ubuntu-noble-dind:1.19.0-rolling-daily

USER root

ARG SOCIAL_ANALYZER_COMMIT=1ba0905e00d054aab833eb3693739c354db09e0f
LABEL org.opencontainers.image.source="https://github.com/qeeqbox/social-analyzer" \
      org.opencontainers.image.revision="${SOCIAL_ANALYZER_COMMIT}"

ENV HOME       /home/kasm-user
ENV STARTUPDIR /dockerstartup
WORKDIR $HOME

# Install Git, curl, notifications, and the Docker Compose plugin
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    curl \
    libnotify-bin \
    docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*


# Clone the Social-Analyzer repo and pin the build to the latest verified main commit.
RUN git clone --depth 1 https://github.com/qeeqbox/social-analyzer.git /opt/social-analyzer && \
    cd /opt/social-analyzer && \
    git fetch --depth 1 origin ${SOCIAL_ANALYZER_COMMIT} && \
    git checkout ${SOCIAL_ANALYZER_COMMIT} && \
    git rev-parse HEAD > /opt/social-analyzer.UPSTREAM_COMMIT && \
    chown -R 1000:0 /opt/social-analyzer

# Copy in our custom startup script and rename it to custom_startup.sh
COPY custom_startup_socialanalyzer.sh $STARTUPDIR/custom_startup.sh
RUN chmod +x $STARTUPDIR/custom_startup.sh && \
    chown 1000:0 $STARTUPDIR/custom_startup.sh

# Switch to non-root for execution
USER 1000
WORKDIR $HOME
