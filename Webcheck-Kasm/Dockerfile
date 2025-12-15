FROM kasmweb/firefox:1.18.0-rolling-daily

USER root

# Set Kasm environment variables
ENV HOME /home/kasm-default-profile
ENV STARTUPDIR /dockerstartup
ENV INST_SCRIPTS $STARTUPDIR/install
WORKDIR $HOME

######### Customize Container Here ###########

# Install prerequisites: apt-transport-https, curl, git, gnupg, wget
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    apt-transport-https \
    curl \
    git \
    gnupg \
    wget && \
    \
    # Install Node.js v21 from Nodesource
    curl -fsSL https://deb.nodesource.com/setup_21.x | bash - && \
    apt-get install -y nodejs && \
    \
    # Install Yarn globally via npm
    npm install -g yarn && \
    rm -rf /var/lib/apt/lists/*

# Clone the Webcheck repository (pinned to v1.0.0), install dependencies, and build the application
RUN git clone --branch 1.0.0 --depth 1 https://github.com/Lissy93/web-check.git /web-check && \
    cd /web-check && \
    yarn install && \
    yarn build

# Set up the custom startup script that starts Webcheck and then launches Firefox in kiosk mode.
# (Ensure this file is in your build context.)
COPY custom_startup_webcheck.sh $STARTUPDIR/custom_startup.sh
RUN chmod +x $STARTUPDIR/custom_startup.sh

# Optimize the desktop environment for a single application. This copies single-app configurations
# and removes the XFCE panel so that only the Webcheck app is visible.
RUN cp $HOME/.config/xfce4/xfconf/single-application-xfce-perchannel-xml/* \
    $HOME/.config/xfce4/xfconf/xfce-perchannel-xml/ && \
    cp /usr/share/backgrounds/bg_kasm.png /usr/share/backgrounds/bg_default.png && \
    apt-get remove -y xfce4-panel

######### End Customizations ###########

# Adjust ownership of the default profile folder and the Webcheck directory so the non-root user can access them
RUN chown -R 1000:0 /web-check && \
    chown 1000:0 $HOME && \
    $STARTUPDIR/set_user_permission.sh $HOME

# Switch to the persistent user profile
ENV HOME /home/kasm-user
WORKDIR $HOME
RUN mkdir -p $HOME && chown -R 1000:0 $HOME

# Switch to non-root user (UID 1000)
USER 1000
