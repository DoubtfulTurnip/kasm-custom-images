FROM kasmweb/ubuntu-noble-dind:1.18.0

USER root

# Kasm environment variables
ENV HOME /home/kasm-default-profile
ENV STARTUPDIR /dockerstartup
WORKDIR $HOME

######### Customize Container Here ###########

# 1) Install OS packages, clone Slasher & seed backend/.env
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    apt-transport-https \
    curl \
    git \
    gnupg \
    wget \
    python3 \
    python3-pip \
    zenity \
    docker-compose && \
    rm -rf /var/lib/apt/lists/* && \
    git clone https://github.com/hexastrike/slasher.git /opt/slasher && \
    cd /opt/slasher && \
    git checkout 47ce2295153c7abe3f6b09bcb31885c617ec60f2 && \
    cd / && \
    cp /opt/slasher/template.env /opt/slasher/backend/.env

# 2) Install Python dependencies
RUN pip3 install --break-system-packages --no-cache-dir \
    -r /opt/slasher/backend/requirements.txt

# 3) Generate a Django SECRET_KEY at build-time and inject into both env files
RUN SECRET_KEY="$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" && \
    sed -i "s|<your-secret-key>|$SECRET_KEY|" /opt/slasher/template.env && \
    sed -i "s|<your-secret-key>|$SECRET_KEY|" /opt/slasher/backend/.env

# 4) Copy the custom startup script
COPY custom_startup_slasher.sh $STARTUPDIR/custom_startup.sh
RUN chmod +x $STARTUPDIR/custom_startup.sh

# 5) Fix permissions for the non-root user
RUN chown -R 1000:0 /opt/slasher && \
    chown -R 1000:0 $HOME && \
    $STARTUPDIR/set_user_permission.sh $HOME

######### End Customizations ###########

# Switch to persistent user profile & non-root
ENV HOME /home/kasm-user
WORKDIR $HOME
RUN mkdir -p $HOME && chown -R 1000:0 $HOME
USER 1000
