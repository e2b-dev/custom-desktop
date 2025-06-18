# E2B Desktop Sandbox Template
#
# This Dockerfile contains the commands to create a computer use sandbox on E2B.
# If you want to make your own template based on this one, make your changes

FROM ubuntu:22.04

# Environment variables:

ENV \
    # Avoid system prompts: \
    DEBIAN_FRONTEND=noninteractive \
    DEBIAN_PRIORITY=high \
    # Pip settings: \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Desktop environment:

RUN yes | unminimize && \
    apt-get update && \
    # X window server:
    apt-get install -y xserver-xorg xorg x11-xserver-utils xvfb x11-utils xauth && \
    # XFCE desktop environment:
    apt-get install -y xfce4 xfce4-goodies && \ 
    # Basic system utilities:
    apt-get install -y util-linux sudo curl git wget && \
    # Pip will be used to install Python packages:
    apt-get install -y python3-pip && \ 
    # Tools used by the desktop SDK:
    apt-get install -y xdotool scrot ffmpeg

# Streaming server:

RUN \
    # VNC: \
    apt-get install -y x11vnc && \
    # NoVNC: \
    git clone --branch e2b-desktop https://github.com/e2b-dev/noVNC.git /opt/noVNC && \
    ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html && \
    # Websockify: \
    apt-get install -y net-tools netcat && \
    pip install numpy && \
    git clone --branch v0.12.0 https://github.com/novnc/websockify /opt/noVNC/utils/websockify

# User applications:

# ~ Make your changes to this template BELOW this line ~

# Set the default terminal
RUN ln -sf /usr/bin/xfce4-terminal.wrapper /etc/alternatives/x-terminal-emulator

# Install standard apps
RUN apt-get install -y x11-apps \
    libreoffice \
    xpdf \
    gedit \
    xpaint \
    tint2 \
    galculator \
    pcmanfm

# Install Firefox
RUN apt-get install -y software-properties-common && \
    add-apt-repository ppa:mozillateam/ppa && \
    apt-get install -y --no-install-recommends \
    firefox-esr

# Copy desktop background for XFCE
COPY ./wallpaper.png /usr/share/backgrounds/xfce/wallpaper.png
RUN mkdir -p /home/user/.config/xfce4/xfconf/xfce-perchannel-xml/
COPY ./xfce4-desktop.xml /home/user/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml

# Install gtk-launch and update desktop database
RUN apt-get install -y libgtk-3-bin && \
    update-desktop-database /usr/share/applications/

# Copy firefox policies
COPY firefox-policies.json /usr/lib/firefox-esr/distribution/policies.json
COPY firefox-autoconfig.js /usr/lib/firefox-esr/defaults/pref/autoconfig.js
COPY firefox.cfg /usr/lib/firefox-esr/firefox.cfg

COPY api /api
RUN pip install hatchling && \
    pip install -e /api

COPY start_command.sh /start_command.sh
RUN chmod +x /start_command.sh
ENTRYPOINT ["/start_command.sh"]