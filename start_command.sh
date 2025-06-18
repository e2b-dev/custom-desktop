#!/bin/bash

# Set display
export DISPLAY=${DISPLAY:-:0}

# Start Xvfb if not running
if ! pgrep -x "Xvfb" > /dev/null; then
    Xvfb $DISPLAY -ac -screen 0 1024x768x24 -nolisten tcp &
    sleep 2
fi

# Start XFCE session if not running
if ! pgrep -x "xfce4-session" > /dev/null; then
    startxfce4 &
    sleep 5
fi

# Start VNC server
x11vnc -bg -display $DISPLAY -forever -wait 50 -shared -rfbport 5900 -nopw \
    -noxdamage -noxfixes -nowf -noscr -ping 1 -repeat -speeds lan &
sleep 2

# Start noVNC server
cd /opt/noVNC/utils && ./novnc_proxy --vnc localhost:5900 --listen 6080 --web /opt/noVNC --heartbeat 30 &
sleep 2

# Start the FastAPI server
cd api && uvicorn main:app --host 0.0.0.0 --port 49999 --workers 1 --no-access-log --no-use-colors --timeout-keep-alive 640