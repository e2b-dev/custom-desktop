import subprocess
import time
import os
import signal
import psutil

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class MousePosition(BaseModel):
    x: int
    y: int

# VNC server configuration
VNC_PORT = 5900
NOVNC_PORT = 6080
DISPLAY = os.getenv("DISPLAY", ":0")

def kill_process_by_name(process_name):
    """Kill all processes with the given name"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if process_name in proc.info['name']:
                os.kill(proc.info['pid'], signal.SIGTERM)
                time.sleep(0.5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def wait_for_process(process_name, timeout=10):
    """Wait for a process to start, with timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            subprocess.run(['pgrep', '-x', process_name], check=True)
            return True
        except subprocess.CalledProcessError:
            time.sleep(0.5)
    return False

@app.get("/start-desktop")
def read_root():
    # Kill any existing VNC processes to avoid conflicts
    kill_process_by_name('x11vnc')
    kill_process_by_name('novnc_proxy')
    
    # Check if Xvfb is running
    try:
        subprocess.run(['pgrep', '-x', 'Xvfb'], check=True)
        xvfb_running = True
    except subprocess.CalledProcessError:
        xvfb_running = False

    if not xvfb_running:
        # Start Xvfb with more robust options
        subprocess.Popen(['Xvfb', DISPLAY, '-ac', '-screen', '0', '1024x768x24', '-nolisten', 'tcp'])
        if not wait_for_process('Xvfb', timeout=10):
            return {"error": "Failed to start Xvfb"}

    # Check if XFCE is running
    try:
        subprocess.run(['pgrep', '-x', 'xfce4-session'], check=True)
        xfce_running = True
    except subprocess.CalledProcessError:
        xfce_running = False

    if not xfce_running:
        # Start XFCE session with proper environment
        env = dict(os.environ, DISPLAY=DISPLAY)
        subprocess.Popen(['startxfce4'], env=env)
        if not wait_for_process('xfce4-session', timeout=15):
            return {"error": "Failed to start XFCE session"}

    # Start VNC server with more stable options
    vnc_cmd = [
        'x11vnc',
        '-bg',
        '-display', DISPLAY,
        '-forever',
        '-wait', '50',
        '-shared',
        '-rfbport', str(VNC_PORT),
        '-nopw',
        '-noxdamage',  # Disable X DAMAGE to avoid compositing issues
        '-noxfixes',   # Disable XFIXES to avoid potential issues
        '-nowf',       # Disable wireframing
        '-noscr',      # Disable scroll detection
        '-ping', '1',  # Add ping to keep connection alive
        '-repeat',     # Enable key repeat
        '-speeds', 'lan'  # Optimize for LAN speeds
    ]
    
    subprocess.Popen(vnc_cmd)
    if not wait_for_process('x11vnc', timeout=10):
        return {"error": "Failed to start VNC server"}

    # Start noVNC server with proper working directory
    novnc_cmd = [
        'cd', '/opt/noVNC/utils', '&&',
        './novnc_proxy',
        '--vnc', f'localhost:{VNC_PORT}',
        '--listen', str(NOVNC_PORT),
        '--web', '/opt/noVNC',
        '--heartbeat', '30'  # Add heartbeat to keep connection alive
    ]
    
    subprocess.Popen(' '.join(novnc_cmd), shell=True)
    time.sleep(2)  # Give noVNC a moment to start

    # Get the host from environment or use localhost
    host = os.getenv("HOST", "localhost")
    stream_url = f"http://{host}:{NOVNC_PORT}/vnc.html?autoconnect=true&resize=scale"

    return {"stream_url": stream_url}

@app.post("/move-mouse")
def move_mouse(position: MousePosition):
    try:
        # Ensure xdotool is installed
        subprocess.run(['which', 'xdotool'], check=True)
        
        # Move mouse to specified coordinates
        subprocess.run(['xdotool', 'mousemove', str(position.x), str(position.y)], check=True)
        return {"status": "success", "message": f"Mouse moved to coordinates ({position.x}, {position.y})"}
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:  # xdotool not found
            raise HTTPException(status_code=500, detail="xdotool is not installed")
        raise HTTPException(status_code=500, detail=f"Failed to move mouse: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")