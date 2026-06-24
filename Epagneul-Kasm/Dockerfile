# syntax=docker/dockerfile:1
FROM kasmweb/ubuntu-noble-dind:1.19.0-rolling-daily

USER root

# Set Kasm environment variables
ENV HOME /home/kasm-default-profile
ENV STARTUPDIR /dockerstartup
ENV INST_SCRIPTS $STARTUPDIR/install
WORKDIR $HOME

######### Customize Container Here ###########

# Create a working folder for and download the docker-compose YAML file (pinned to 0.4.1).
RUN mkdir -p /epagneul && \
    git clone --branch 0.4.1 --depth 1 https://github.com/jurelou/epagneul.git /epagneul


RUN apt-get update && apt-get install -y --no-install-recommends libnotify-bin && \
    rm -rf /var/lib/apt/lists/*

# Smoke test: verify epagneul was cloned and git log works
RUN test -d /epagneul && git -C /epagneul log --oneline -1

# Pre-build Epagneul service containers at image build time.
# Storing images as a tar archive means startup loads them in seconds
# instead of spending 10+ minutes building from source on every session.
RUN --security=insecure bash -c '
    set -euo pipefail
    dockerd --host=unix:///var/run/docker.sock >/tmp/dockerd-prebuild.log 2>&1 &
    DOCKERD_PID=$!
    for i in $(seq 1 60); do docker info >/dev/null 2>&1 && break || sleep 1; done
    docker info >/dev/null 2>&1 || { echo "dockerd failed to start:"; cat /tmp/dockerd-prebuild.log; exit 1; }
    cd /epagneul
    docker pull neo4j:4.4.2
    docker compose -f docker-compose-prod.yml -p epagneul build backend frontend
    docker save epagneul-backend:latest epagneul-frontend:latest neo4j:4.4.2 \
        | gzip > /epagneul-prebuilt.tar.gz
    docker system prune -af
    kill $DOCKERD_PID || true
    wait $DOCKERD_PID 2>/dev/null || true
'

# Copy the custom startup script into the container.
COPY custom_startup_epagneul.sh $STARTUPDIR/custom_startup.sh
RUN chmod +x $STARTUPDIR/custom_startup.sh

######### End Customizations ###########

# Fix permissions for Kasm's default profile.
RUN chown 1000:0 $HOME && \
    $STARTUPDIR/set_user_permission.sh $HOME

# Switch HOME to the persistent user profile.
ENV HOME /home/kasm-user
WORKDIR $HOME
RUN mkdir -p $HOME && chown -R 1000:0 $HOME

USER 1000
