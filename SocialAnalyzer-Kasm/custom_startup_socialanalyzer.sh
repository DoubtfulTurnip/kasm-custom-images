#!/usr/bin/env bash
# Startup for Social-Analyzer in Kasm using custom_startup.sh

# 1) Signal Kasm that desktop is ready
/usr/bin/desktop_ready

# 2) Ensure Docker daemon is running (DinD base auto-launches dockerd)
sudo service docker start
sleep 5

# 3) Change to the cloned repo (contains docker-compose.yml)
cd /opt/social-analyzer

notify-send -t 60000 "SocialAnalyzer" "Starting SocialAnalyzer services…"

# 4) Bring up Selenium hub/node + Social-Analyzer web container
docker compose up -d

# 5) Wait for the web UI to become responsive instead of using a fixed sleep
echo "[*] Waiting for SocialAnalyzer to be ready..."
for i in {1..60}; do
    if curl -sf http://localhost:9005/app.html > /dev/null 2>&1; then
        echo "[+] SocialAnalyzer is ready"
        break
    fi
    echo "[-] Still waiting... ($i/60)"
    sleep 2
done

# 6) Prepare Chrome preferences to avoid first-run dialogs
CHROME_PREF_DIR="$HOME/.config/google-chrome/Default"
if [ ! -f "$CHROME_PREF_DIR/Preferences" ]; then
  mkdir -p "$CHROME_PREF_DIR"
  echo '{}' > "$CHROME_PREF_DIR/Preferences"
fi
sed -i 's/"show_welcome_page":[^,]*/"show_welcome_page":false/' "$CHROME_PREF_DIR/Preferences" || true
sed -i 's/"first_run_tabs":[^]]*/"first_run_tabs":[]/' "$CHROME_PREF_DIR/Preferences" || true

# 7) Launch the Social-Analyzer web UI in Chrome
google-chrome \
  --start-maximized \
  http://0.0.0.0:9005/app.html &
