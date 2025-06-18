import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class MousePosition(BaseModel):
    x: int
    y: int

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