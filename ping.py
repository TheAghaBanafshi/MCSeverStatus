import os
from mcstatus import JavaServer

INPUT_FILE = "server.txt"
OUTPUT_FILE = "ping.txt"
TIMEOUT = 5

def extract_motd(motd):
    if isinstance(motd, dict):
        text = motd.get("text", "")
        for e in motd.get("extra", []):
            if isinstance(e, dict):
                text += e.get("text", "")
            else:
                text += str(e)
        return text
    return str(motd)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"'{INPUT_FILE}' not found!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        servers = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    results = []
    for addr in servers:
        try:
            server = JavaServer.lookup(addr, timeout=TIMEOUT)
            status = server.status()
            online = status.players.online
            maxp = status.players.max
            motd = extract_motd(status.description).replace("\n", " ").replace('"', "'")

            # نسخه‌های جدید mcstatus از icon استفاده می‌کنن، نه favicon
            icon = ""
            if hasattr(status, "icon") and status.icon:
                icon = status.icon
                print(f"[DEBUG] {addr}: icon found, length = {len(icon)}")
            elif hasattr(status, "favicon") and status.favicon:
                icon = status.favicon
                print(f"[DEBUG] {addr}: favicon found, length = {len(icon)}")
            else:
                print(f"[DEBUG] {addr}: no icon attribute found or value is None")

            line = f'{addr} - Online - {online}/{maxp} players - "{motd}"'
            if icon:
                line += f' | {icon}'
            results.append(line)
            print(f"[OK] {addr} -> {online}/{maxp} (icon: {'yes' if icon else 'no'})")
        except Exception as e:
            results.append(f"{addr} - Offline")
            print(f"[FAIL] {addr} -> {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(results) + "\n")

    print(f"\nSaved {len(results)} results to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
