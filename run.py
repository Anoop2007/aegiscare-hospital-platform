import uvicorn
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting CareAura Health OS on http://127.0.0.1:{port} (bound to {host}:{port})")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True, reload_dirs=["backend"])
