import asyncio
import subprocess
import httpx
from src.core.config import settings

# Games and heavy 3d apps to watch out for
GAME_PROCESS_KEYWORDS = {
    # Wuthering Waves
    "client-win64-shipping.exe", "wuthering waves.exe", "launcher.exe",
    # Hoyoverse
    "genshinimpact.exe", "starrail.exe", "zenlesszonezero.exe", "honkai3rd.exe",
    # AAA & competitive
    "cyberpunk2077.exe", "eldenring.exe", "blackmythwukong.exe", "valorant-win64-shipping.exe",
    "cs2.exe", "dota2.exe", "overwatch.exe", "fortniteclient-win64-shipping.exe",
    "r5apex.exe", "gta5.exe", "gta6.exe", "callofduty.exe", "cod.exe",
    "warframe.x64.exe", "destiny2.exe", "helldivers2.exe", "monstertrans.exe",
    # 3D engines
    "unrealeditor.exe", "unity.exe", "blender.exe"
}

is_game_active = False

def check_running_games() -> str | None:
    try:
        cmd = ["nvidia-smi", "--query-compute-apps=process_name", "--format=csv,noheader"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.strip().splitlines():
                clean_path = line.strip().lower()
                for kw in GAME_PROCESS_KEYWORDS:
                    if kw in clean_path:
                        exe_name = clean_path.split("\\")[-1]
                        return exe_name
    except Exception:
        pass
    return None

async def unload_ollama_vram():
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(
                f"{settings.LOCAL_LLM_URL}/api/generate",
                json={"model": settings.MODEL_CHAT, "keep_alive": 0}
            )
            print(f"[VRAM WATCHDOG] Model '{settings.MODEL_CHAT}' evicted from VRAM.")
    except Exception as e:
        print(f"[VRAM WATCHDOG ERROR] Failed to unload model: {e}")

async def start_gpu_game_watchdog():
    global is_game_active
    print("[VRAM WATCHDOG] Game monitor active.")

    while True:
        try:
            detected_game = check_running_games()

            if detected_game:
                if not is_game_active:
                    is_game_active = True
                    print(f"\n🎮 [GAME DETECTED: {detected_game}] Releasing VRAM for game performance.\n")
                    await unload_ollama_vram()
            else:
                if is_game_active:
                    is_game_active = False
                    print(f"\n🎮 [GAME CLOSED] VRAM is free again.\n")

        except Exception:
            pass

        await asyncio.sleep(4)
