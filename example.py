from e2b import Sandbox

sandbox = Sandbox("desktop-groq")

print("Streaming URL: ", f"https://{sandbox.get_host(6080)}/vnc.html")