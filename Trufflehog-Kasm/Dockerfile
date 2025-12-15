FROM kasmweb/ubuntu-noble-desktop:1.17.0

USER root

# ─── Remove unneeded desktop apps, install scripts, and .desktop launchers ───
RUN set -eux; \
    apt-get update; \
    apt-get remove -y --purge \
    'firefox*' \
    'sublime-text*' \
    'code*' \
    'nextcloud*' \
    'remmina*' \
    'onlyoffice*' \
    'signal*' \
    'gimp*' \
    'zoom*' \
    'ansible*' \
    'telegram*' \
    'thunderbird*' \
    'slack*' || true; \
    rm -rf \
    /ubuntu/install/firefox \
    /ubuntu/install/sublime_text \
    /ubuntu/install/vs_code \
    /ubuntu/install/nextcloud \
    /ubuntu/install/remmina \
    /ubuntu/install/only_office \
    /ubuntu/install/signal \
    /ubuntu/install/gimp \
    /ubuntu/install/zoom \
    /ubuntu/install/ansible \
    /ubuntu/install/telegram \
    /ubuntu/install/thunderbird \
    /ubuntu/install/slack; \
    find /usr/share/applications -type f \( \
    -iname '*firefox*.desktop' -o \
    -iname '*sublime*.desktop' -o \
    -iname '*code*.desktop' -o \
    -iname '*nextcloud*.desktop' -o \
    -iname '*remmina*.desktop' -o \
    -iname '*onlyoffice*.desktop' -o \
    -iname '*signal*.desktop' -o \
    -iname '*gimp*.desktop' -o \
    -iname '*zoom*.desktop' -o \
    -iname '*telegram*.desktop' -o \
    -iname '*thunderbird*.desktop' -o \
    -iname '*slack*.desktop' \
    \) -delete; \
    rm -f /home/kasm-default-profile/Desktop/*.desktop \
    /home/kasm-user/Desktop/*.desktop || true; \
    apt-get autoremove -y; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# ─── Kasm environment variables ────────────────────────────────────────────
ENV HOME=/home/kasm-default-profile \
    STARTUPDIR=/dockerstartup \
    INST_SCRIPTS=$STARTUPDIR/install
WORKDIR $HOME

# ─── Install system dependencies (including gobuster) ──────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    curl \
    git \
    libnotify-bin \
    gobuster && \
    rm -rf /var/lib/apt/lists/*

# ─── Copy and prepare the app ───────────────────────────────────────────────
COPY . /app
WORKDIR /app

# Create Python virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt streamlit

# ─── Install TruffleHog v3.92.3 as binary ──────────────────────────────────
RUN curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | \
    sh -s -- -b /usr/local/bin v3.92.3

# ─── Ensure kasm-user can access /app ──────────────────────────────────────
RUN chown -R 1000:0 /app

# ─── Kasm custom startup ───────────────────────────────────────────────────
COPY custom_startup_trufflehog.sh $STARTUPDIR/custom_startup.sh
RUN chmod +x $STARTUPDIR/custom_startup.sh

# Fix permissions for default profile
RUN chown 1000:0 $HOME && \
    $STARTUPDIR/set_user_permission.sh $HOME

# ─── Switch to persistent user profile ────────────────────────────────────
ENV HOME=/home/kasm-user
WORKDIR $HOME
RUN mkdir -p $HOME && chown -R 1000:0 $HOME

USER 1000
