#!/bin/bash
# Enhanced BloodHound startup script for Kasm (background execution)
# This script runs automatically when the workspace starts

set -euo pipefail

# Configuration
readonly BLOODHOUND_DIR="/bloodhound"
readonly DESKTOP_DIR="/home/kasm-user/Desktop"
readonly LOGFILE="$DESKTOP_DIR/BloodHound_startup.log"
readonly STATUS_FILE="$DESKTOP_DIR/BloodHound_Status.txt"
readonly CREDS_FILE="$DESKTOP_DIR/BloodHound_Credentials.txt"
readonly MAX_RETRIES=3
COMPOSE_TIMEOUT=300  # 5 minutes for docker compose up (scaled by configure_resources on low-RAM hosts)
WAIT_UI_TIMEOUT=180  # seconds to poll for web UI (scaled by configure_resources on low-RAM hosts)

# Logging function (file-only since user won't see terminal)
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${timestamp} [${level}] ${message}" >> "$LOGFILE"
}

# Update status file function
update_status() {
    local status="$1"
    local message="$2"
    
    cat > "$STATUS_FILE" << EOF
=== BloodHound CE Status ===
Last Updated: $(date)
Status: $status

$message

=== Access Information ===
URL: http://localhost:8080/ui/login
Username: admin
Password: See BloodHound_Credentials.txt

=== Container Management ===
Project Name: ${PROJECT_NAME:-"Not started"}
Check logs: docker compose -p "${PROJECT_NAME:-bloodhound}" logs
Stop services: docker compose -p "${PROJECT_NAME:-bloodhound}" down
EOF
    
    # Make sure desktop files are readable
    chmod 644 "$STATUS_FILE" 2>/dev/null || true
}

# Error handler that updates status file
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    log "ERROR" "Startup failed at line $line_number with exit code $exit_code"
    
    update_status "❌ FAILED" "BloodHound startup failed. Check the log file for details.

Common issues:
• Docker service not starting
• Insufficient disk space
• Network connectivity problems
• Container conflicts

Log file: $LOGFILE"
    
    notify-send -u critical -t 0 "BloodHound Startup Failed" \
        "Setup encountered an error. Check BloodHound_Status.txt on desktop for details." || true
    
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Cleanup function
cleanup_existing() {
    docker info >/dev/null 2>&1 || return 0  # skip if Docker not yet running
    log "INFO" "Cleaning up any existing BloodHound containers"

    # Stop and remove any existing bloodhound containers
    docker ps -aq --filter "name=bloodhound" | xargs -r docker rm -f >/dev/null 2>&1 || true

    # Clean up any orphaned compose projects
    docker compose -f "$BLOODHOUND_DIR/docker-compose.yml" down --remove-orphans >/dev/null 2>&1 || true
}

# Detect available RAM and write a docker-compose.override.yml tuned to the host
configure_resources() {
    local total_ram_mb
    total_ram_mb=$(free -m | awk '/^Mem:/{print $2}')
    log "INFO" "Detected ${total_ram_mb}MB total RAM"

    local heap pagecache mem_limit query_limit
    if (( total_ram_mb < 4096 )); then
        heap="512m"; pagecache="512m"; mem_limit="1536m"; query_limit=1
        COMPOSE_TIMEOUT=$(( COMPOSE_TIMEOUT * 2 ))
        WAIT_UI_TIMEOUT=$(( WAIT_UI_TIMEOUT * 2 ))
        log "INFO" "Low-resource host: extended timeouts to compose=${COMPOSE_TIMEOUT}s ui=${WAIT_UI_TIMEOUT}s"
    elif (( total_ram_mb < 8192 )); then
        heap="1g"; pagecache="1g"; mem_limit="3g"; query_limit=2
    else
        heap="2g"; pagecache="2g"; mem_limit="5g"; query_limit=4
    fi

    cat > "$BLOODHOUND_DIR/docker-compose.override.yml" << EOF
services:
  graph-db:
    environment:
      - NEO4J_dbms_memory_heap_initial__size=${heap}
      - NEO4J_dbms_memory_heap_max__size=${heap}
      - NEO4J_dbms_memory_pagecache__size=${pagecache}
    deploy:
      resources:
        limits:
          memory: ${mem_limit}
  bloodhound:
    environment:
      - bhe_graph_query_memory_limit=${query_limit}
EOF

    log "INFO" "Resource config: Neo4j heap=${heap}, pagecache=${pagecache}, limit=${mem_limit}, BH query_limit=${query_limit}GB"
}

# Start Docker service
start_docker_service() {
    log "INFO" "Starting Docker service"
    update_status "🚀 STARTING" "Starting Docker service..."
    
    if docker info >/dev/null 2>&1; then
        log "INFO" "Docker is already running"
        return 0
    fi
    
    local retry_count=0
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        if sudo service docker start >/dev/null 2>&1; then
            # Wait for Docker daemon to be ready
            for ((i=1; i<=30; i++)); do
                if docker info >/dev/null 2>&1; then
                    log "INFO" "Docker service ready"
                    return 0
                fi
                sleep 1
            done
        fi
        
        ((retry_count++))
        log "WARN" "Docker start attempt $retry_count failed"
        sleep 3
    done
    
    log "ERROR" "Failed to start Docker service"
    return 1
}

# Start BloodHound services
start_bloodhound() {
    log "INFO" "Starting BloodHound services"
    update_status "⏳ DEPLOYING" "Starting BloodHound containers... This takes 3-5 minutes.

Please wait while:
• Database initializes
• Web interface starts
• Services synchronize

Do not close this workspace yet!"
    
    # Generate unique project name
    PROJECT_NAME="bloodhound_$(date +%s)"
    export PROJECT_NAME
    log "INFO" "Using project name: $PROJECT_NAME"
    
    # Change to BloodHound directory
    cd "$BLOODHOUND_DIR"
    
    # Verify compose file exists
    if [[ ! -f "docker-compose.yml" ]]; then
        log "ERROR" "docker-compose.yml not found"
        return 1
    fi
    
    # Start services with extended timeout
    timeout "$COMPOSE_TIMEOUT" docker compose -p "$PROJECT_NAME" up -d || {
        log "ERROR" "Failed to start BloodHound within timeout"
        # Get container logs for debugging
        docker compose -p "$PROJECT_NAME" logs --tail=20 >> "$LOGFILE" 2>&1 || true
        return 1
    }
    
    log "INFO" "BloodHound containers started, waiting for services..."
}

# Wait for BloodHound to be ready
wait_for_bloodhound() {
    log "INFO" "Waiting for BloodHound web interface"
    update_status "⌛ INITIALIZING" "BloodHound is starting up...

Web interface: Initializing
Database: Connecting
Authentication: Preparing

This usually takes 2-3 minutes."
    
    # Wait for web interface to respond
    for ((i=1; i<=WAIT_UI_TIMEOUT; i++)); do
        if curl -sf --max-time 3 "http://localhost:8080/ui/login" >/dev/null 2>&1; then
            log "SUCCESS" "BloodHound web interface is ready"
            return 0
        fi
        
        # Update status every 30 seconds
        if ((i % 30 == 0)); then
            update_status "⌛ INITIALIZING" "Still starting up... (${i}s elapsed)

This is normal for first startup.
BloodHound needs time to:
• Initialize the Neo4j database
• Set up authentication
• Start the web server"
        fi
        
        sleep 1
    done
    
    log "ERROR" "BloodHound web interface did not become ready"
    return 1
}

# Extract initial password
extract_password() {
    log "INFO" "Extracting initial password"
    
    # Wait up to 2 minutes for password to appear in logs
    for ((i=1; i<=120; i++)); do
        local logs=$(docker compose -p "$PROJECT_NAME" logs --tail 100 2>/dev/null || echo "")
        local password=$(echo "$logs" | grep -i "Initial Password Set To:" | head -n 1 | sed -n 's/.*Initial Password Set To:\s*\([^[:space:]#]*\).*/\1/p' | tr -d '[:space:]')

        if [[ -n "$password" ]]; then
            log "SUCCESS" "Password extracted successfully"
            
            # Create credentials file
            cat > "$CREDS_FILE" << EOF
=== BloodHound CE Login Credentials ===
Generated: $(date)

🌐 URL: http://localhost:8080/ui/login
👤 Username: admin
🔑 Password: $password

=== Getting Started Guide ===

1. DATA COLLECTION:
   • Use SharpHound.exe on Windows domain systems
   • Use BloodHound.py for remote collection
   • Upload .zip files via the UI

2. ANALYSIS:
   • Built-in queries in the "Analysis" tab
   • Custom Cypher queries for advanced analysis
   • Node information panel for detailed data

3. COMMON QUERIES:
   • "Find all Domain Admins"
   • "Shortest Path to Domain Admins"
   • "Find Kerberoastable Users"

=== Container Management ===
Project: $PROJECT_NAME
Status: docker compose -p "$PROJECT_NAME" ps
Logs: docker compose -p "$PROJECT_NAME" logs
Stop: docker compose -p "$PROJECT_NAME" down

=== Resources ===
📚 Docs: https://bloodhound.readthedocs.io/
🐙 GitHub: https://github.com/BloodHoundAD/BloodHound
💬 Slack: https://bloodhoundgang.slack.com/
EOF
            
            chmod 644 "$CREDS_FILE"
            return 0
        fi
        
        sleep 1
    done
    
    log "WARN" "Could not extract password, creating manual instructions"
    
    cat > "$CREDS_FILE" << EOF
=== BloodHound CE Login ===
Generated: $(date)

🌐 URL: http://localhost:8080/ui/login
👤 Username: admin
🔑 Password: **CHECK LOGS**

To find the password, open a terminal and run:
docker compose -p "$PROJECT_NAME" logs | grep -i "Initial Password"

Project Name: $PROJECT_NAME
EOF
    
    chmod 644 "$CREDS_FILE"
    return 0
}

# Final setup and launch
finalize_setup() {
    log "INFO" "Finalizing BloodHound setup"
    
    # Verify everything is working
    local running_containers=$(docker compose -p "$PROJECT_NAME" ps -q | wc -l)
    
    update_status "✅ READY" "BloodHound CE is ready to use!

🌐 Access: http://localhost:8080/ui/login
📋 Credentials: See BloodHound_Credentials.txt
📊 Containers: $running_containers running
📝 Logs: $LOGFILE

BloodHound will open automatically in your browser."
    
    # Launch browser after a brief delay
    sleep 1
    google-chrome --start-maximized --no-first-run http://localhost:8080/ui/login >/dev/null 2>&1 &

    # Final success notification
    notify-send -t 15000 "🩸 BloodHound Ready!" \
        "Web interface: http://localhost:8080/ui/login
📋 Login details are on your desktop
🚀 Browser opening automatically" || true
    
    log "SUCCESS" "BloodHound startup completed successfully"
}

# Main execution
main() {
    # Ensure desktop directory exists
    mkdir -p "$DESKTOP_DIR"
    
    # Initialize log
    cat > "$LOGFILE" << EOF
=== BloodHound CE Startup Log ===
Started: $(date)
Workspace: $(hostname)
User: $(whoami)
=====================================

EOF
    
    log "INFO" "Starting BloodHound CE deployment"
    
    # Initial notification
    notify-send -t 10000 "🩸 BloodHound Starting" \
        "Deploying BloodHound CE...
This will take 3-5 minutes.
Check your desktop for progress updates." || true

    # Initial status
    update_status "🚀 STARTING" "Initializing BloodHound CE startup...

This process typically takes 3-5 minutes.
Status updates will appear here automatically."

    # Execute startup sequence
    configure_resources
    cleanup_existing
    start_docker_service
    start_bloodhound

    # Extract password concurrently while waiting for the web UI — the password is
    # logged early during BloodHound init, well before the UI becomes reachable.
    # Run in a subshell with the ERR trap reset so a fallback return code doesn't
    # trigger the parent's error handler.
    ( trap - ERR; extract_password ) &
    PASS_PID=$!

    wait_for_bloodhound

    wait $PASS_PID || log "WARN" "Password extraction had issues, but continuing"

    finalize_setup
}

# Execute main function, redirect output to avoid Kasm console noise
main "$@" 2>&1
