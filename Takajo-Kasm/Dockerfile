FROM kasmweb/ubuntu-noble-desktop:1.18.0

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

# Set environment variables
ENV HOME=/home/kasm-default-profile \
    STARTUPDIR=/dockerstartup
WORKDIR $HOME

# 1) Install runtime dependencies, notifications & PCRE
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl unzip inotify-tools python3 python3-pip python3-venv \
    git libnotify-bin libpcre3 libpcre3-dev && \
    rm -rf /var/lib/apt/lists/*

# 2) Install Hayabusa v3.7.0
RUN curl -L \
    https://github.com/Yamato-Security/hayabusa/releases/download/v3.7.0/hayabusa-3.7.0-lin-x64-gnu.zip \
    -o /tmp/hayabusa.zip && \
    unzip /tmp/hayabusa.zip -d /tmp/hayabusa && \
    mv /tmp/hayabusa/*lin-x64-gnu /usr/local/bin/hayabusa && \
    chmod +x /usr/local/bin/hayabusa && \
    rm -rf /tmp/hayabusa /tmp/hayabusa.zip

# 3) Clone Hayabusa rules
RUN git clone --depth=1 \
    https://github.com/Yamato-Security/hayabusa-rules.git \
    /opt/hayabusa-rules && \
    ln -s /opt/hayabusa-rules "$HOME/rules"

# 4) Install Takajō v2.10.0 into HOME and ensure permissions
RUN curl -L \
    https://github.com/Yamato-Security/takajo/releases/download/v2.10.0/takajo-2.10.0-lin-x64-gnu.zip \
    -o /tmp/takajo.zip && \
    unzip /tmp/takajo.zip -d "$HOME/takajo" && \
    chmod +x "$HOME/takajo/takajo-2.10.0-lin-x64-gnu" && \
    chown -R 1000:0 "$HOME/takajo" && \
    chmod -R a+rX "$HOME/takajo" && \
    # Wrapper to always run from takajo dir
    printf '#!/usr/bin/env bash\ncd "$HOME"/takajo && exec "$HOME"/takajo/takajo-2.10.0-lin-x64-gnu "$@"\n' > /usr/local/bin/takajo && \
    chmod +x /usr/local/bin/takajo && \
    rm -rf /tmp/takajo.zip

RUN curl -L "https://github.com/WithSecureLabs/chainsaw/releases/download/v2.13.1/chainsaw_all_platforms+rules.zip" \
    -o /tmp/chainsaw_all_platforms+rules.zip && \
    unzip /tmp/chainsaw_all_platforms+rules.zip -d /tmp && \
    rm /tmp/chainsaw_all_platforms+rules.zip && \
    mv /tmp/chainsaw /opt/Chainsaw && \
    mv /opt/Chainsaw/chainsaw_x86_64-unknown-linux-gnu /usr/local/bin/chainsaw && \
    chmod +x /usr/local/bin/chainsaw && \
    ln -s /opt/Chainsaw/sigma    "$HOME/chainsaw-sigma-rules" && \
    ln -s /opt/Chainsaw/mappings "$HOME/chainsaw-mappings"    && \
    ln -s /opt/Chainsaw/rules    "$HOME/chainsaw-rules"






# 5) Prepare reports directory
RUN mkdir -p /reports

# 6) Copy custom startup script
COPY custom_startup_takajo.sh $STARTUPDIR/custom_startup.sh
RUN chmod +x $STARTUPDIR/custom_startup.sh

# 7) Fix ownership for rules and reports
RUN chown -R 1000:0 /reports /opt/hayabusa-rules

# 8) Switch to non-root user
USER 1000
WORKDIR $HOME

# Kasm auto-executes custom_startup.sh on launch
