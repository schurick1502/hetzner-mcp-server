"""SSH Web-Terminal via WebSocket."""

import asyncio
import os
import sys
import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

router = APIRouter()

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


def get_ssh_key_path():
    """SSH-Key-Pfad ermitteln."""
    key_path = os.environ.get("DOCKER_MONITOR_KEY", "")
    if key_path and os.path.exists(key_path):
        return key_path
    # Fallback: Standard-SSH-Key
    home = os.path.expanduser("~")
    for name in ["id_rsa", "id_ed25519"]:
        path = os.path.join(home, ".ssh", name)
        if os.path.exists(path):
            return path
    return None


@router.websocket("/ws/{server_ip}")
async def ssh_websocket(websocket: WebSocket, server_ip: str):
    """WebSocket-Endpoint für SSH-Terminal-Verbindung."""
    await websocket.accept()

    if not PARAMIKO_AVAILABLE:
        await websocket.send_text("\r\n*** paramiko nicht installiert. SSH nicht verfügbar. ***\r\n")
        await websocket.close()
        return

    key_path = get_ssh_key_path()
    if not key_path:
        await websocket.send_text("\r\n*** Kein SSH-Key gefunden. Bitte DOCKER_MONITOR_KEY setzen. ***\r\n")
        await websocket.close()
        return

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    channel = None

    try:
        # SSH-Verbindung aufbauen
        username = os.environ.get("SSH_USER", "root")
        ssh_port = int(os.environ.get("SSH_PORT", "22"))

        await websocket.send_text(f"Verbinde mit {server_ip}...\r\n")

        # Load key
        try:
            pkey = paramiko.Ed25519Key.from_private_key_file(key_path)
        except Exception:
            try:
                pkey = paramiko.RSAKey.from_private_key_file(key_path)
            except Exception:
                pkey = paramiko.DSSKey.from_private_key_file(key_path)

        ssh.connect(
            hostname=server_ip,
            port=ssh_port,
            username=username,
            pkey=pkey,
            timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )

        # Shell öffnen
        channel = ssh.invoke_shell(term='xterm-256color', width=120, height=40)
        channel.settimeout(0.1)

        await websocket.send_text(f"Verbunden mit {server_ip} als {username}\r\n")

        # Background-Thread: SSH → WebSocket
        stop_event = threading.Event()
        loop = asyncio.get_event_loop()

        async def read_ssh():
            """Daten vom SSH-Channel lesen und an WebSocket senden."""
            while not stop_event.is_set():
                try:
                    if channel.recv_ready():
                        data = channel.recv(4096)
                        if data:
                            await websocket.send_text(data.decode('utf-8', errors='replace'))
                        else:
                            break
                    else:
                        await asyncio.sleep(0.05)
                except Exception:
                    break

        # SSH-Lese-Task starten
        read_task = asyncio.create_task(read_ssh())

        # WebSocket → SSH
        try:
            while True:
                data = await websocket.receive_text()
                if channel and channel.active:
                    channel.send(data)
                else:
                    break
        except WebSocketDisconnect:
            pass
        finally:
            stop_event.set()
            read_task.cancel()
            try:
                await read_task
            except asyncio.CancelledError:
                pass

    except paramiko.AuthenticationException:
        await websocket.send_text("\r\n*** Authentifizierung fehlgeschlagen. SSH-Key prüfen. ***\r\n")
    except paramiko.SSHException as e:
        await websocket.send_text(f"\r\n*** SSH-Fehler: {str(e)} ***\r\n")
    except TimeoutError:
        await websocket.send_text(f"\r\n*** Verbindungs-Timeout zu {server_ip} ***\r\n")
    except Exception as e:
        await websocket.send_text(f"\r\n*** Fehler: {str(e)} ***\r\n")
    finally:
        if channel:
            channel.close()
        ssh.close()
        try:
            await websocket.close()
        except Exception:
            pass
