FROM kasmweb/ubuntu-noble-dind:1.19.0-rolling-daily

USER root

# Set Kasm environment variables
ENV HOME /home/kasm-default-profile
ENV STARTUPDIR /dockerstartup
ENV INST_SCRIPTS $STARTUPDIR/install
WORKDIR $HOME

######### Customize Container Here ###########

# Create a working folder for BloodHound and download the docker-compose YAML file (pinned commit).
RUN mkdir -p /bloodhound && \
    curl -fL "https://raw.githubusercontent.com/SpecterOps/bloodhound/170bde5418f17a526c8bfd9662b234cd35a93779/examples/docker-compose/docker-compose.yml" \
    -o /bloodhound/docker-compose.yml

RUN apt-get update && apt-get install -y --no-install-recommends libnotify-bin && \
    rm -rf /var/lib/apt/lists/*

# Smoke test: verify docker is available and compose file was downloaded
RUN which docker && test -f /bloodhound/docker-compose.yml

# Copy the custom startup script into the container.
COPY custom_startup_bloodhound.sh $STARTUPDIR/custom_startup.sh
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
