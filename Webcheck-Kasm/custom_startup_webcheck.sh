#!/bin/bash
# Custom startup script for single-app Webcheck using Firefox

/usr/bin/desktop_ready

cd /web-check

# Serve the pre-built production output instead of running the dev server.
# yarn build was already run at image build time; yarn preview starts in ~1s.
yarn preview --host 0.0.0.0 &

echo "[*] Waiting for Webcheck to become responsive..."
for i in {1..30}; do
    if curl -s http://localhost:4321 > /dev/null; then
        echo "[+] Webcheck is ready"
        break
    fi
    echo "[-] Still waiting... ($i)"
    sleep 1
done

firefox --kiosk http://localhost:4321 &
