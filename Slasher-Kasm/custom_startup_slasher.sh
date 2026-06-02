#!/bin/bash
# Custom startup script for Slasher in Kasm


/usr/bin/desktop_ready


sudo service docker start
sleep 5


cd /opt/slasher


cp template.env .env
cp template.env backend/.env

SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
sed -i "s|<your-secret-key>|$SECRET_KEY|" .env
sed -i "s|<your-secret-key>|$SECRET_KEY|" backend/.env


VT_KEY=$(zenity --entry \
  --title="Slasher: VirusTotal API Key" \
  --text="Enter your VirusTotal API Key:" \
  --hide-text)
if [ -z "$VT_KEY" ]; then
  zenity --error --text="VirusTotal API key is required. Exiting."
  exit 1
fi
sed -i '/^VIRUSTOTAL_API_KEY=/d' .env
echo "VIRUSTOTAL_API_KEY=$VT_KEY" >> .env
sed -i '/^VIRUSTOTAL_API_KEY=/d' backend/.env
echo "VIRUSTOTAL_API_KEY=$VT_KEY" >> backend/.env


notify-send -t 800000 "Slasher" "Starting Slasher services…"


docker compose up -d --build --force-recreate


docker compose exec -T slasher_backend python3 manage.py migrate --noinput


docker compose restart slasher_backend


sleep 3


google-chrome \
  --start-maximized \
  http://localhost:3000 &
