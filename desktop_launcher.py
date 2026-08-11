import subprocess
import sys
import time
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def is_port_open(port: int = 8000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def main():
    print("========================================")
    print("       Aibou Desktop Launcher           ")
    print("========================================")

    # 1. Start FastAPI backend if not already running
    backend_proc = None
    if not is_port_open(8000):
        print("\n[LAUNCHER] Starting local Aibou backend server...")
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        
        # Wait up to 10s for backend to initialize
        for _ in range(20):
            if is_port_open(8000):
                print("[LAUNCHER] Backend server online!")
                break
            time.sleep(0.5)
    else:
        print("[LAUNCHER] Backend server already active on port 8000.")

    # 2. Launch native Tauri desktop app window
    compiled_app = ROOT / "frontend" / "src-tauri" / "target" / "release" / "app.exe"
    if compiled_app.exists():
        print(f"[LAUNCHER] Launching desktop app: {compiled_app.name}")
        try:
            subprocess.run([str(compiled_app)])
        except KeyboardInterrupt:
            pass
        finally:
            if backend_proc:
                print("\n[LAUNCHER] Shutting down backend server...")
                backend_proc.terminate()
    else:
        print("[LAUNCHER] Launching via Tauri dev...")
        try:
            subprocess.run(["npx", "tauri", "dev"], cwd=str(ROOT / "frontend"), shell=True)
        except KeyboardInterrupt:
            pass
        finally:
            if backend_proc:
                print("\n[LAUNCHER] Shutting down backend server...")
                backend_proc.terminate()

if __name__ == "__main__":
    main()
