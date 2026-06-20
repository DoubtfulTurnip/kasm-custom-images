#!/usr/bin/env bash
# Startup for Social-Analyzer in Kasm using custom_startup.sh

set -Eeuo pipefail

APP_DIR="/opt/social-analyzer"
APP_URL="http://localhost:9005/app.html"
LOG_DIR="$HOME/Desktop/Downloads"
LOG_FILE="$LOG_DIR/socialanalyzer-startup.log"
DOCKER_INFO_LOG="/tmp/socialanalyzer-docker-info.log"
DOCKER_CMD=(docker)
APP_READY_ATTEMPTS=300
APP_READY_SLEEP_SECONDS=2

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

log() {
  echo "[$(date --iso-8601=seconds)] $*"
}

notify() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send -t 60000 "SocialAnalyzer" "$*" || log "Notification failed: $*"
  else
    log "Notification unavailable: $*"
  fi
}

dump_compose_diagnostics() {
  log "Docker Compose service status:"
  "${DOCKER_CMD[@]}" compose ps || true
  log "Recent Docker Compose logs:"
  "${DOCKER_CMD[@]}" compose logs --tail=200 || true
}

fail() {
  local message="$1"
  log "ERROR: $message"
  notify "$message"
  if [ "${PWD:-}" = "$APP_DIR" ] && command -v docker >/dev/null 2>&1; then
    dump_compose_diagnostics
  fi
  exit 1
}

check_docker_ready() {
  # Prefer sudo because Docker-in-Docker often exposes the socket to root only.
  # Use timeout so a wedged daemon/socket cannot stall the startup loop for minutes.
  if timeout 5 sudo docker info >"$DOCKER_INFO_LOG" 2>&1; then
    DOCKER_CMD=(sudo docker)
    return 0
  fi

  if timeout 5 docker info >"$DOCKER_INFO_LOG" 2>&1; then
    DOCKER_CMD=(docker)
    return 0
  fi

  return 1
}

check_app_ready() {
  curl -fsS --connect-timeout 2 --max-time 5 "$APP_URL" >/dev/null 2>&1
}

# 1) Signal Kasm that desktop is ready
/usr/bin/desktop_ready || true

# 2) Ensure Docker daemon is running
log "Starting Docker service..."
sudo service docker start || fail "Docker service failed to start. See $LOG_FILE"

log "Waiting for Docker daemon to become ready..."
for i in {1..30}; do
  if check_docker_ready; then
    log "Docker is ready using: ${DOCKER_CMD[*]}"
    break
  fi
  log "Docker is not ready yet ($i/30)"
  sleep 2
done

if ! check_docker_ready; then
  log "Last Docker readiness error:"
  tail -n 40 "$DOCKER_INFO_LOG" || true
  fail "Docker did not become ready. See $LOG_FILE"
fi

# 3) Change to the Compose directory
cd "$APP_DIR" || fail "Could not change to $APP_DIR"

if [ -f /opt/social-analyzer.UPSTREAM_COMMIT ]; then
  log "SocialAnalyzer upstream commit: $(cat /opt/social-analyzer.UPSTREAM_COMMIT)"
fi

notify "Starting SocialAnalyzer services..."

# 4) Pull and start the prebuilt SocialAnalyzer web container.
log "Pulling prebuilt SocialAnalyzer app image..."
"${DOCKER_CMD[@]}" compose pull --quiet || fail "Docker Compose failed to pull the prebuilt SocialAnalyzer app image. See $LOG_FILE"

log "Starting Docker Compose services..."
"${DOCKER_CMD[@]}" compose up -d --remove-orphans || fail "Docker Compose failed to start SocialAnalyzer services. See $LOG_FILE"

# 5) Wait for the web UI to become responsive before launching a browser.
log "Waiting for SocialAnalyzer to become responsive at $APP_URL..."
ready=false
for ((i = 1; i <= APP_READY_ATTEMPTS; i++)); do
  if check_app_ready; then
    ready=true
    log "SocialAnalyzer is ready"
    break
  fi
  log "Still waiting for SocialAnalyzer... ($i/$APP_READY_ATTEMPTS)"
  sleep "$APP_READY_SLEEP_SECONDS"
done

[ "$ready" = "true" ] || fail "SocialAnalyzer did not become ready. See $LOG_FILE"

# 6) Prepare Chrome preferences to avoid first-run dialogs
CHROME_PREF_DIR="$HOME/.config/google-chrome/Default"
if [ ! -f "$CHROME_PREF_DIR/Preferences" ]; then
  mkdir -p "$CHROME_PREF_DIR"
  echo '{}' > "$CHROME_PREF_DIR/Preferences"
fi
sed -i 's/"show_welcome_page":[^,]*/"show_welcome_page":false/' "$CHROME_PREF_DIR/Preferences" || true
sed -i 's/"first_run_tabs":[^]]*/"first_run_tabs":[]/' "$CHROME_PREF_DIR/Preferences" || true

# 7) Launch the Social-Analyzer web UI
log "Opening SocialAnalyzer at $APP_URL"
if command -v google-chrome >/dev/null 2>&1; then
  google-chrome --no-sandbox --disable-dev-shm-usage --start-maximized "$APP_URL" &
elif command -v chromium-browser >/dev/null 2>&1; then
  chromium-browser --no-sandbox --disable-dev-shm-usage --start-maximized "$APP_URL" &
elif command -v firefox >/dev/null 2>&1; then
  firefox "$APP_URL" &
else
  notify "SocialAnalyzer is ready at $APP_URL, but no supported browser was found."
  log "No supported browser was found. Open $APP_URL manually."
fi