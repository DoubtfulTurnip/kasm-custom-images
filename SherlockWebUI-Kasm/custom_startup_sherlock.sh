#!/bin/bash
# Custom startup script for Streamlit-based Sherlock WebUI in Kasm

/usr/bin/desktop_ready

# Start Tor so the Tor-mode proxy is available when requested.
# Tor takes 10-30s to establish circuits; starting it early avoids delays.
sudo service tor start &

echo "[*] Launching Streamlit Sherlock UI..."
cd /app
source /app/venv/bin/activate
streamlit run app.py --server.address 0.0.0.0 --server.port 5000 --server.headless true &

echo "[*] Waiting for Streamlit to become responsive..."
for i in {1..20}; do
    if curl -s http://localhost:5000 > /dev/null; then
        echo "[+] Streamlit is ready"
        break
    fi
    echo "[-] Still waiting... ($i)"
    sleep 1
done

echo "[*] Opening in Chrome..."
google-chrome --no-sandbox --disable-dev-shm-usage --start-maximized http://localhost:5000 &
