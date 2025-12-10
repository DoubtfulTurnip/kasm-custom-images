FROM kasmweb/ubuntu-noble-desktop:1.18.0

USER root

# Kasm environment variables
ENV HOME=/home/kasm-default-profile \
    STARTUPDIR=/dockerstartup \
    INST_SCRIPTS=$STARTUPDIR/install
WORKDIR $HOME

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-pip python3-venv curl git tor \
        build-essential libjpeg-dev zlib1g-dev libpng-dev && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python dependencies (including Sherlock v0.15.0)
RUN python3 -m venv /app/venv
WORKDIR /app
COPY requirements.txt .
RUN . /app/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Copy application and startup script
COPY app.py custom_startup_sherlock.sh /app/
RUN mkdir -p $STARTUPDIR && \
    mv /app/custom_startup_sherlock.sh $STARTUPDIR/custom_startup.sh && \
    chmod +x $STARTUPDIR/custom_startup.sh

# Fix permissions for Kasm profiles
RUN chown -R 1000:0 /home/kasm-default-profile /app

# Switch to persistent user profile
ENV HOME=/home/kasm-user
WORKDIR $HOME
RUN mkdir -p $HOME && chown -R 1000:0 $HOME

USER 1000
# Kasm will auto-execute custom_startup.sh