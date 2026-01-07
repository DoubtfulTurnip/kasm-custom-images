FROM kasmweb/ubuntu-noble-dind:1.18.0-rolling-daily

USER root

ENV HOME       /home/kasm-user
ENV STARTUPDIR /dockerstartup
WORKDIR $HOME

# Install only Git, curl, and the Docker Compose plugin
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*


# Clone the entire Social-Analyzer repo (includes docker-compose.yml) - using main branch (no releases available)
RUN git clone --depth 1 https://github.com/qeeqbox/social-analyzer.git /opt/social-analyzer && \
    chown -R 1000:0 /opt/social-analyzer

# Copy in our custom startup script and rename it to custom_startup.sh
COPY custom_startup_socialanalyzer.sh $STARTUPDIR/custom_startup.sh
RUN chmod +x $STARTUPDIR/custom_startup.sh && \
    chown 1000:0 $STARTUPDIR/custom_startup.sh

# Switch to non-root for execution
USER 1000
WORKDIR $HOME
