#!/usr/bin/env python3
import asyncio, csv, os, signal, time, hashlib
from datetime import datetime, timezone
from bleak import BleakScanner

# --- Parámetros ---
SESSION_TIMEOUT_S = 120           # segundos sin ver un dispositivo para cerrar su sesión
FLUSH_INTERVAL_S = 5              # cada cuántos segundos buscamos sesiones caducadas
WRITE_THROTTLE_S = 5              # escribe como mucho 1 línea cada 5 s por dispositivo en "seen"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STORE_RAW_ADDRESS = True          # si hay SALT, no se guarda MAC en claro
SALT = os.environ.get("BLE_SALT", "")

# --- Estado ---
sessions = {}                     # addr -> {start_ts, last_ts, rssi_sum, rssi_count}
last_write = {}                   # addr -> last_seen_write_ts (para throttle)
running = True

# --- Utilidades ---
def ts_now():
    return time.time()

def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

def anon_id(addr: str) -> str:
    if not SALT:
        return addr
    return hashlib.sha256((SALT + addr).encode()).hexdigest()[:16]

def sessions_csv_path(ts=None):
    d = datetime.fromtimestamp(ts or ts_now(), tz=timezone.utc).strftime("%Y-%m-%d")
    return os.path.join(DATA_DIR, f"sessions-{d}.csv")

def seen_csv_path(ts=None):
    d = datetime.fromtimestamp(ts or ts_now(), tz=timezone.utc).strftime("%Y-%m-%d")
    return os.path.join(DATA_DIR, f"seen-{d}.csv")

def ensure_header(path, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(cols)

def write_session(addr, start_ts, end_ts, mean_rssi):
    path = sessions_csv_path(start_ts)
    ensure_header(
        path,
        ["id", "start_utc", "end_utc", "duration_s", "mean_rssi"]
        + (["mac"] if STORE_RAW_ADDRESS and not SALT else []),
    )
    row = [
        anon_id(addr),
        iso(start_ts),
        iso(end_ts),
        round(end_ts - start_ts),
        mean_rssi,
    ]
    if STORE_RAW_ADDRESS and not SALT:
        row.append(addr)
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow(row)

def write_seen(addr, rssi, ts):
    path = seen_csv_path(ts)
    ensure_header(
        path,
        ["id", "utc", "rssi"] + (["mac"] if STORE_RAW_ADDRESS and not SALT else []),
    )
    row = [anon_id(addr), iso(ts), rssi]
    if STORE_RAW_ADDRESS and not SALT:
        row.append(addr)
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow(row)

# --- Callback de anuncios BLE ---
def handle_advertisement(device, advertisement_data):
    addr = device.address
    now = ts_now()
    rssi = (advertisement_data.rssi if advertisement_data and advertisement_data.rssi is not None else 0)

    # Throttle de escrituras en "seen" (máx. 1 línea/WRITE_THROTTLE_S por dispositivo)
    if now - last_write.get(addr, 0) >= WRITE_THROTTLE_S:
        write_seen(addr, rssi, now)
        print(f"Visto {addr} RSSI={rssi}")
        last_write[addr] = now

    # Actualizar sesión (siempre, para medias correctas)
    s = sessions.get(addr)
    if s:
        s["last_ts"] = now
        s["rssi_sum"] += rssi
        s["rssi_count"] += 1
    else:
        sessions[addr] = {
            "start_ts": now,
            "last_ts": now,
            "rssi_sum": rssi,
            "rssi_count": 1,
        }

# --- Bucle de cierre de sesiones ---
async def flush_loop():
    while running:
        await asyncio.sleep(FLUSH_INTERVAL_S)
        now = ts_now()
        stale = []
        for addr, s in list(sessions.items()):
            if now - s["last_ts"] >= SESSION_TIMEOUT_S:
                stale.append((addr, s))
        for addr, s in stale:
            mean_rssi = int(s["rssi_sum"] / max(1, s["rssi_count"]))
            write_session(addr, s["start_ts"], s["last_ts"], mean_rssi)
            # Mensaje útil para ver que se cierran sesiones
            print(f"[SESSION] {addr} dur={round(s['last_ts']-s['start_ts'])}s mean_rssi={mean_rssi}")
            sessions.pop(addr, None)

def stop(*_):
    global running
    running = False

# --- Main ---
async def main():
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    os.makedirs(DATA_DIR, exist_ok=True)
    scanner = BleakScanner(handle_advertisement)  # importante: pasar el callback directamente
    await scanner.start()
    flusher = asyncio.create_task(flush_loop())
    try:
        while running:
            await asyncio.sleep(1)
    finally:
        await scanner.stop()
        await asyncio.sleep(0.1)
        now = ts_now()
        for addr, s in list(sessions.items()):
            mean_rssi = int(s["rssi_sum"] / max(1, s["rssi_count"]))
            write_session(addr, s["start_ts"], now, mean_rssi)
            sessions.pop(addr, None)
        flusher.cancel()
        try:
            await flusher
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
