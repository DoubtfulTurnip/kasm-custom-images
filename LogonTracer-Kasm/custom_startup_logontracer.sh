#!/bin/bash
# Custom startup script for LogonTracer in a full desktop environment using Google Chrome.

sudo service docker start

sleep 5

# Display a desktop notification to inform the user.
notify-send -t 60000 "LogonTracer is starting" "Please wait while LogonTracer services are being deployed."

# Generate a unique container name using the current timestamp
CONTAINER_NAME="logontracer_$(date +%s)"
echo "Using container name: $CONTAINER_NAME"

# Run the LogonTracer container with a unique name (pinned to v1.6.1).
docker container run --name "$CONTAINER_NAME" --detach \
    --publish=7474:7474 \
    --publish=7687:7687 \
    --publish=8080:8080 \
    -e LTHOSTNAME=127.0.0.1 \
    jpcertcc/docker-logontracer:v1.6.1

sleep 60

echo "LogonTracer Username: neo4j" > /home/kasm-user/Desktop/LogonTracer_Password.txt
echo "LogonTracer Password: password" >> /home/kasm-user/Desktop/LogonTracer_Password.txt

notify-send -t 30000 "LogonTracer has started" "The login information is located on the desktop."

google-chrome --start-maximized http://127.0.0.1:8080 &
