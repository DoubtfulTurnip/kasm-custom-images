#!/usr/bin/env bash
# custom_startup.sh — EVTX → Hayabusa → Takajō dynamic HTML server with extended analysis and list outputs

set -euo pipefail
LOG="[DEBUG] custom_startup.sh $$"
echo "$LOG starting"
trap '{ echo "$LOG exiting"; [[ -n "${TKA_PID-}" ]] && kill "$TKA_PID"; }' EXIT

# Wait for Kasm desktop ready
desktop_ready &>/dev/null || true

# Stub notify-send if unavailable
if ! command -v notify-send &>/dev/null; then
  function notify-send() { :; }
fi

# Update Hayabusa detection rules in the background so they stay current.
# Runs silently; failures (e.g. no network) are non-fatal.
echo "$LOG updating Hayabusa rules in background"
git -C /opt/hayabusa-rules pull --ff-only --quiet 2>/dev/null &

# ------------------------------------------------------------
# CONFIG
HOME_DIR="$HOME"
WATCH_DIR="$HOME_DIR/Desktop/Uploads"
TMP_JSONL="/tmp/timeline.jsonl"
RULES_PATH="$HOME/rules"
RULES_CONF="$HOME/rules/config"
CHAINSAW_RULES="$HOME/chainsaw-rules"
CHAINSAW_MAPPINGS="$HOME/chainsaw-mappings/sigma-event-logs-all.yml"
CHAINSAW_SIGMA="$HOME/chainsaw-sigma-rules"
REPORTS_DIR="/reports"
STATIC_DIR="$REPORTS_DIR/static"
HTML_DB="$REPORTS_DIR/html-server.sqlite"
PORT=8000
# Timestamp for extended reports in Downloads folder
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
EXT_DIR="$HOME_DIR/Desktop/Downloads/TakajoReports_$TIMESTAMP"

# Prepare directories
mkdir -p "$WATCH_DIR" "$REPORTS_DIR" "$EXT_DIR"
# Redirect logs to file
LOGFILE="$EXT_DIR/custom_startup_$TIMESTAMP.log"
exec > >(tee -a "$LOGFILE") 2>&1
echo "$LOG logging to $LOGFILE"
cd "$HOME_DIR"
# Initial notification (10s)
notify-send -t 10000 "Takajō" "Watching for .evtx in $WATCH_DIR and subfolders"

# Wait until uploads settle: resets 30s timer on each new event
wait_for_uploads() {
  echo "$LOG waiting for uploads to finish (30s inactivity)"
  while true; do
    if file=$(inotifywait -r -e create -e moved_to -e close_write --format '%w%f' -t 30 "$WATCH_DIR" 2>/dev/null); then
      echo "$LOG detected new file: $file, resetting timer"
      continue
    else
      echo "$LOG no new uploads in 30s, proceeding"
      break
    fi
  done
}

run_all() {
  echo "$LOG starting upload wait"
  wait_for_uploads

  echo "$LOG cleaning timeline & DB"
  rm -f "$TMP_JSONL" "$HTML_DB"

  echo "$LOG converting EVTX to JSONL"
  hayabusa json-timeline \
    --directory "$WATCH_DIR" \
    --output "$TMP_JSONL" \
    --no-wizard --clobber --JSONL-output \
    --profile super-verbose --min-level informational \
    --quiet --rules-config "$RULES_CONF"

  if [[ ! -s "$TMP_JSONL" ]]; then
    echo "$LOG no data; exiting"
    return
  fi

  echo "$LOG clearing old static reports"
  rm -rf "$STATIC_DIR"

  echo "$LOG running automagic"
  takajo automagic -t "$TMP_JSONL" -o "$STATIC_DIR" --quiet

  echo "$LOG starting HTML server"
  takajo html-server \
    --timeline "$TMP_JSONL" \
    --rulepath "$RULES_PATH" --port "$PORT" \
    --clobber --quiet --sqliteoutput "$HTML_DB" &
  TKA_PID=$!

  # Open browser once
  if command -v google-chrome &>/dev/null; then
    google-chrome --no-sandbox --disable-dev-shm-usage \
      --start-maximized "http://localhost:$PORT" &
  else
    xdg-open "http://localhost:$PORT" || nohup firefox "http://localhost:$PORT" &
  fi

  # Extended analysis outputs
  for cmd in stack-cmdlines stack-computers stack-dns stack-ip-addresses stack-logons \
             stack-processes stack-services stack-tasks stack-users; do
    takajo "$cmd" -t "$TMP_JSONL" -o "$EXT_DIR/${cmd}.csv" --quiet
  done

  # Timeline CSV commands
  takajo timeline-logon -t "$TMP_JSONL" -o "$EXT_DIR/timeline-logon.csv" -c -l -a --quiet
  takajo timeline-partition-diagnostic -t "$TMP_JSONL" -o "$EXT_DIR/timeline-partition-diagnostic.csv" --quiet
  takajo timeline-suspicious-processes -t "$TMP_JSONL" -o "$EXT_DIR/timeline-suspicious-processes.csv" --quiet
  takajo timeline-tasks -t "$TMP_JSONL" -o "$EXT_DIR/timeline-tasks.csv" --quiet

  # TTP commands
  takajo ttp-summary -t "$TMP_JSONL" -o "$EXT_DIR/ttp-summary.csv" --quiet
  takajo ttp-visualize -t "$TMP_JSONL" -o "$EXT_DIR/ttp-visualize.json" --quiet

  # List outputs
  takajo list-domains -t "$TMP_JSONL" -o "$EXT_DIR/domains.txt" --quiet
  takajo list-hashes -t "$TMP_JSONL" -o "$EXT_DIR/hashes" --quiet
  takajo list-ip-addresses -t "$TMP_JSONL" -o "$EXT_DIR/ipAddresses.txt" --quiet

  # Run Chainsaw hunt after all processing
  echo "$LOG running Chainsaw hunt"
  chainsaw hunt "$WATCH_DIR" \
    --sigma   "$CHAINSAW_SIGMA" \
    --rule    "$CHAINSAW_RULES" \
    --mapping "$CHAINSAW_MAPPINGS" \
    --csv --skip-errors \
    --output "$EXT_DIR/chainsaw_hunt"

  # Create a zip of all exported files
  echo "$LOG creating ZIP archive"
  ZIPFILE="$HOME_DIR/Desktop/Downloads/TakajoReports_$TIMESTAMP.zip"
  zip -r "$ZIPFILE" "$EXT_DIR"
  echo "$LOG created zip: $ZIPFILE"

  # Final notifications (10s)
  notify-send -t 10000 "Takajō" "Extended reports available: $EXT_DIR"
  notify-send -t 10000 "Takajō" "Zipped archive created: $ZIPFILE"
}

# -----------------------------
# Debounced EVTX watcher & runner
# -----------------------------
debounce_pid=""

inotifywait -m -r \
  -e close_write,moved_to \
  --format '%w%f' \
  --exclude '.*\.uploading$' \
  "$WATCH_DIR" \
| while read -r evfile; do
    if [[ "$evfile" == *.evtx ]]; then
      echo "$LOG detected EVTX: $evfile, resetting debounce timer"

      # cancel any existing pending run
      [[ -n $debounce_pid ]] && kill "$debounce_pid" 2>/dev/null || true

      # start a new 30s timer: if it completes, call run_all
      (
        sleep 30 && \
        echo "$LOG no new EVTX in 30s; starting analysis" && \
        notify-send -t 10000 "Takajō" "No new EVTX in 30s, beginning analysis" && \
        run_all
      ) &
      debounce_pid=$!
    fi
  done
