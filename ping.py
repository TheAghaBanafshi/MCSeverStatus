import os
import json
import urllib.request
import urllib.error
from mcstatus import JavaServer

INPUT_FILE = "server.txt"
OUTPUT_FILE = "ping.txt"
TIMEOUT = 5

# هدر User-Agent برای API واسط (شبیه مرورگر کروم)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def extract_motd(motd):
    """استخراج MOTD از پاسخ mcstatus"""
    if isinstance(motd, dict):
        text = motd.get("text", "")
        for e in motd.get("extra", []):
            if isinstance(e, dict):
                text += e.get("text", "")
            else:
                text += str(e)
        return text
    return str(motd)

def ping_with_mcstatus(addr):
    """تلاش اول: پینگ مستقیم با mcstatus"""
    try:
        server = JavaServer.lookup(addr, timeout=TIMEOUT)
        status = server.status()
        online = status.players.online
        maxp = status.players.max
        motd = extract_motd(status.description).replace("\n", " ").replace('"', "'")

        # آیکون سرور
        icon = ""
        if hasattr(status, "icon") and status.icon:
            icon = status.icon
        elif hasattr(status, "favicon") and status.favicon:
            icon = status.favicon

        return {
            "success": True,
            "online": online,
            "max": maxp,
            "motd": motd,
            "icon": icon,
            "method": "mcstatus"
        }
    except Exception as e:
        print(f"[mcstatus] {addr} failed: {e}")
        return {"success": False}

def ping_with_api(addr):
    """تلاش دوم: استفاده از API واسط mcsrvstat.us با User-Agent"""
    try:
        url = f"https://api.mcsrvstat.us/3/{addr}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if not data.get("online"):
            return {"success": False, "reason": "offline"}

        online = data.get("players", {}).get("online", 0)
        maxp = data.get("players", {}).get("max", 0)
        
        # MOTD از API
        motd_data = data.get("motd", {})
        motd = ""
        if isinstance(motd_data, dict):
            motd = motd_data.get("clean", "") or motd_data.get("raw", "")
        elif isinstance(motd_data, list):
            motd = " ".join(motd_data)
        
        motd = motd.replace("\n", " ").replace('"', "'")

        # آیکون
        icon = data.get("icon", "")

        return {
            "success": True,
            "online": online,
            "max": maxp,
            "motd": motd,
            "icon": icon,
            "method": "mcsrvstat.us"
        }
    except Exception as e:
        print(f"[API] {addr} failed: {e}")
        return {"success": False, "reason": str(e)}

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"'{INPUT_FILE}' not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        servers = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    results = []
    for addr in servers:
        print(f"\n--- Processing {addr} ---")
        
        # تلاش اول: mcstatus
        result = ping_with_mcstatus(addr)
        
        # اگه mcstatus جواب نداد، برو سراغ API
        if not result["success"]:
            print(f"[Fallback] Trying API for {addr}...")
            result = ping_with_api(addr)
        
        if result["success"]:
            line = f'{addr} - Online - {result["online"]}/{result["max"]} players - "{result["motd"]}"'
            if result["icon"]:
                line += f' | {result["icon"]}'
            results.append(line)
            print(f"[OK] {addr} -> {result["online"]}/{result["max"]} (via {result["method"]}, icon: {'yes' if result["icon"] else 'no'})")
        else:
            results.append(f"{addr} - Offline")
            print(f"[FAIL] {addr} -> Offline")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(results) + "\n")

    print(f"\nSaved {len(results)} results to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
