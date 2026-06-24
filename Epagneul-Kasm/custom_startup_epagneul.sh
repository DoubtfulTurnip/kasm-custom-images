#!/bin/bash
# Epagneul startup script for Kasm
# Service images are pre-built into the workspace image; startup loads them via docker load.

set -euo pipefail

# Configuration
readonly DESKTOP_DIR="$HOME/Desktop"
readonly LOGFILE="$DESKTOP_DIR/Epagneul_startup.log"
readonly STATUS_FILE="$DESKTOP_DIR/Epagneul_Status.txt"
readonly EPAGNEUL_DIR="/epagneul"
readonly PREBUILT_ARCHIVE="/epagneul-prebuilt.tar.gz"
readonly WEB_UI_URL="http://localhost:8080"
readonly BACKEND_URL="http://localhost:8000"
readonly NEO4J_URL="http://localhost:7474"

# Logging functions
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*" | tee -a "$LOGFILE"; }
error() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" | tee -a "$LOGFILE"; }
warn() { echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] $*" | tee -a "$LOGFILE"; }

# Status update function
update_status() {
    local status="$1"
    local details="${2:-}"
    
    cat > "$STATUS_FILE" <<EOF
=== Epagneul Windows Event Log Analyzer ===
Last Updated: $(date)
Status: $status

$details

=== Service Endpoints ===
🌐 Web UI: $WEB_UI_URL
⚙️  Backend API: $BACKEND_URL  
🗄️  Neo4j Database: $NEO4J_URL

=== Container Management ===
Project Name: ${PROJECT_NAME:-"Not started"}
View containers: docker compose -p "${PROJECT_NAME:-epagneul}" ps
View logs: docker compose -p "${PROJECT_NAME:-epagneul}" logs  
Stop services: docker compose -p "${PROJECT_NAME:-epagneul}" down

Log file: $LOGFILE
EOF
    
    chmod 644 "$STATUS_FILE" 2>/dev/null || true
}

# Error handler
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    error "Startup failed at line $line_number with exit code $exit_code"
    
    update_status "❌ FAILED" "Epagneul startup failed at line $line_number.

Common issues:
• Docker service failed to start
• Port conflicts (8080, 8000, 7474 already in use)  
• Network connectivity issues
• Build failures due to dependency conflicts
• Insufficient memory for Docker builds

Check the log file for detailed error information."
    
    notify-send -u critical -t 0 "Epagneul Startup Failed" \
        "Event log analyzer failed to start. Check Epagneul_Status.txt on desktop." || true

    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Clean up existing containers
cleanup_existing() {
    docker info >/dev/null 2>&1 || return 0  # skip if Docker not yet running
    log "Cleaning up any existing Epagneul containers"
    
    # Remove containers that might conflict
    local patterns=("epagneul" "frontend" "backend" "neo4j")
    for pattern in "${patterns[@]}"; do
        local containers=$(docker ps -aq --filter "name=${pattern}" 2>/dev/null || true)
        if [[ -n "$containers" ]]; then
            log "Removing existing containers matching: $pattern"
            echo "$containers" | xargs docker rm -f >/dev/null 2>&1 || true
        fi
    done
}

# Start Docker service
start_docker() {
    log "Starting Docker service"
    update_status "🚀 INITIALIZING" "Starting Docker service for Epagneul..."
    
    sudo service docker start || true
    
    for i in {1..30}; do
        if docker info >/dev/null 2>&1; then
            log "Docker service is ready"
            return 0
        fi
        sleep 1
    done
    
    error "Docker failed to start within 30 seconds"
    return 1
}

# Determine which compose file to use
find_compose_file() {
    log "Looking for Epagneul compose file"
    
    cd "$EPAGNEUL_DIR"
    
    # Try different possible compose file names
    local compose_files=("docker-compose-prod.yml" "docker-compose.yml" "compose.yml")
    
    for file in "${compose_files[@]}"; do
        if [[ -f "$file" ]]; then
            COMPOSE_FILE="$file"
            log "Found compose file: $COMPOSE_FILE"
            return 0
        fi
    done
    
    error "No docker compose file found in $EPAGNEUL_DIR"
    ls -la "$EPAGNEUL_DIR" | tee -a "$LOGFILE"
    return 1
}

# Start the application stack
start_stack() {
    PROJECT_NAME="epagneul"
    export COMPOSE_PROJECT_NAME="$PROJECT_NAME"
    log "Using project name: $PROJECT_NAME"
    log "Compose file: $COMPOSE_FILE"

    if [[ -f "$PREBUILT_ARCHIVE" ]]; then
        log "Loading pre-built Epagneul images from archive..."
        update_status "⏳ LOADING" "Loading pre-built Epagneul containers...

Expected startup time: under 1 minute.

Services being loaded:
• 🌐 Frontend web interface
• ⚙️ Backend API
• 🗄️ Neo4j Graph Database"

        docker load -i "$PREBUILT_ARCHIVE"
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
        log "Services started successfully from pre-built archive"
    else
        # Fallback: runtime source build (slow — pre-built archive should normally be present)
        log "Pre-built archive not found — falling back to runtime source build (this will take several minutes)"
        update_status "⏳ BUILDING" "Building Epagneul containers from source (fallback mode)...

This may take 5-10 minutes on first run."

        if timeout 1200 docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d --build; then
            log "Services started successfully via runtime build"
        else
            error "Failed to start services"
            docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs --tail=50 | tee -a "$LOGFILE" 2>&1 || true
            return 1
        fi
    fi
}

# Wait for all services to be healthy
wait_for_services() {
    log "Waiting for services to become healthy"
    update_status "⌛ STARTING" "Services are initializing...

🗄️ Neo4j Database: Initializing (1-2 minutes)
⚙️ Backend API: Starting (30-60s)
🌐 Web Interface: Starting (30-60s)"
    
    local max_wait=300  # 5 minutes total wait time
    local services_ready=0
    
    for ((i=1; i<=max_wait; i++)); do
        local neo4j_ready=0
        local backend_ready=0
        local frontend_ready=0
        
        # Check each service
        if curl -sf --max-time 3 "$NEO4J_URL" >/dev/null 2>&1; then
            neo4j_ready=1
        fi

        if curl -sf --max-time 3 "$BACKEND_URL" >/dev/null 2>&1; then
            backend_ready=1
        fi

        if curl -sf --max-time 3 "$WEB_UI_URL" >/dev/null 2>&1; then
            frontend_ready=1
        fi
        
        # Update status every 30 seconds
        if ((i % 30 == 0)); then
            local status_msg="Service startup in progress... (${i}s elapsed)

🗄️ Neo4j Database: $([ $neo4j_ready -eq 1 ] && echo "✅ Ready" || echo "⏳ Starting")
⚙️ Backend API: $([ $backend_ready -eq 1 ] && echo "✅ Ready" || echo "⏳ Starting")
🌐 Web Interface: $([ $frontend_ready -eq 1 ] && echo "✅ Ready" || echo "⏳ Starting")

Containers are initializing."
            
            update_status "⌛ STARTING" "$status_msg"
        fi
        
        # Check if all services are ready
        if [[ $neo4j_ready -eq 1 && $backend_ready -eq 1 && $frontend_ready -eq 1 ]]; then
            log "All services are healthy and ready"
            services_ready=1
            break
        fi
        
        sleep 1
    done
    
    if [[ $services_ready -eq 0 ]]; then
        warn "Not all services became ready within timeout"
        # Show container status for debugging
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps | tee -a "$LOGFILE"
        
        # The frontend is the user-facing endpoint — require it as the minimum
        if [[ $frontend_ready -eq 1 ]]; then
            warn "Frontend is ready; backend/Neo4j may still be initialising"
        else
            error "No services are responding, startup may have failed"
            docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs --tail=50 | tee -a "$LOGFILE"
            return 1
        fi
    fi
    
    return 0
}

# Launch browser
launch_browser() {
    log "Launching browser for Epagneul web interface"
    # wait_for_services already confirmed the frontend is ready; one last best-effort check
    curl -sf --max-time 3 "$WEB_UI_URL" >/dev/null 2>&1 || true

    google-chrome \
        --no-sandbox \
        --disable-dev-shm-usage \
        --start-maximized \
        --no-first-run \
        --no-default-browser-check \
        --disable-extensions \
        "$WEB_UI_URL" >/dev/null 2>&1 &
    log "Browser launched"
}

# Create user guide
create_user_guide() {
    log "Creating user guide"
    
    cat > "$DESKTOP_DIR/Epagneul_User_Guide.txt" <<EOF
=== Epagneul Windows Event Log Analyzer ===
Started: $(date)

🎯 PURPOSE:
Epagneul is a powerful tool for visualizing and investigating Windows event logs
using graph-based analysis to reveal relationships between hosts, users, and logon events.

🌐 ACCESS POINTS:
• Web UI: $WEB_UI_URL (Main interface)
• Backend API: $BACKEND_URL (REST API)
• Neo4j Browser: $NEO4J_URL (Graph database)

🚀 DEPLOYMENT FEATURES:
• Pre-built container images loaded at startup (fast)
• Uses official Epagneul docker-compose configuration
• Reliable container orchestration with Docker-in-Docker
• Expected startup time: under 1 minute

📊 KEY FEATURES:
• Graph visualization of Windows logon events
• Timeline analysis of authentication activities
• Relationship mapping between hosts and accounts
• Support for EVTX and JSONL file formats
• Neo4j graph database for complex queries

🔧 GETTING STARTED:
1. Upload Windows event logs (.evtx files) via the web interface
2. Explore the graph visualization to see relationships
3. Use timeline filters to focus on specific periods
4. Investigate suspicious patterns and lateral movement
5. Export findings for reporting

📋 COMMON WORKFLOWS:
• Incident Response: Upload logs from compromised systems
• Threat Hunting: Look for patterns across multiple systems  
• Compliance Auditing: Analyze authentication activities
• Forensic Analysis: Timeline reconstruction of events

⚙️ CONTAINER MANAGEMENT:
Project: $PROJECT_NAME
Status: docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps  
Logs: docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
Stop: docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
Restart: docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart

📚 RESOURCES:
• GitHub: https://github.com/jurelou/epagneul
• Neo4j Documentation: https://neo4j.com/docs/
• Windows Event ID Reference: Microsoft Security Auditing
• EVTX Format: Windows Event Log Analysis

💡 TROUBLESHOOTING:
• If web UI doesn't load: Check $WEB_UI_URL in browser; Neo4j takes ~60s to initialise
• If upload fails: Verify backend API at $BACKEND_URL
• If graphs don't appear: Ensure Neo4j at $NEO4J_URL, check data import
• For slow performance: Check container resources, restart services if needed

🔍 ANALYSIS TIPS:
• Start with small log files to familiarize yourself with the interface
• Use meaningful names when organizing your investigations
• Combine with other forensic tools for comprehensive analysis
• Export interesting findings for documentation and reporting

Log file: $LOGFILE
Status file: $STATUS_FILE
EOF
    
    chmod 644 "$DESKTOP_DIR/Epagneul_User_Guide.txt"
    log "User guide created successfully"
}

# Finalize setup
finalize_setup() {
    log "Finalizing Epagneul setup"
    
    local running_containers=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps -q --filter "status=running" | wc -l)
    local total_containers=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps -q | wc -l)
    
    update_status "✅ READY" "Epagneul is ready for Windows event log analysis!

🌐 Access: $WEB_UI_URL
📖 User Guide: See Epagneul_User_Guide.txt
📊 Services: $running_containers/$total_containers containers running

🚀 QUICK START:
1. Browser opened automatically to web interface
2. Upload Windows .evtx files for analysis  
3. Explore graph visualization and timeline
4. Check desktop files for detailed documentation

Ready to investigate Windows event logs!"
    
    # Create user guide
    create_user_guide
    
    # Desktop shortcut as a persistent convenience launcher
    cat > "$DESKTOP_DIR/Open_Epagneul.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Open Epagneul
Comment=Launch Epagneul Web Interface
Exec=google-chrome --no-sandbox $WEB_UI_URL
Icon=web-browser
Terminal=false
Categories=Network;WebBrowser;
EOF
    chmod +x "$DESKTOP_DIR/Open_Epagneul.desktop"

    # Success notification
    notify-send -t 15000 "🔍 Epagneul Ready!" \
        "Windows Event Log Analyzer is ready!
🌐 Web Interface: $WEB_UI_URL
📖 Check desktop for user guide and status" || true
    
    log "Epagneul startup completed successfully"
}

# Main execution
main() {
    # Ensure desktop directory exists
    mkdir -p "$DESKTOP_DIR"
    
    # Initialize log file
    cat > "$LOGFILE" <<EOF
=== Epagneul Startup Log ===
Started: $(date)
Workspace: $(hostname)
User: $(whoami)
===========================

EOF
    
    log "Starting Epagneul deployment"

    # Initial notification
    notify-send -t 10000 "🔍 Epagneul Starting" \
        "Windows Event Log Analyzer starting...
Expected time: under 1 minute
Progress updates on desktop" || true

    # Initial status
    update_status "🚀 INITIALIZING" "Starting Epagneul...

Features:
• Graph-based Windows event log analysis
• Timeline visualization
• Relationship mapping
• Neo4j backend for complex queries

Status will update automatically."

    # Execute startup sequence
    cleanup_existing
    start_docker
    find_compose_file
    start_stack
    wait_for_services
    launch_browser
    finalize_setup

    log "All startup tasks completed successfully"
}

# Execute main function with error handling
main "$@" 2>&1
