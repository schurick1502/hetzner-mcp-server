"""Docker Monitoring API Routes - Remote Docker container monitoring via SSH."""

import os
import json
import asyncio
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel


class CleanupRequest(BaseModel):
    command: str
import paramiko

router = APIRouter()

# SSH Key Path
SSH_KEY_PATH = os.getenv("DOCKER_MONITOR_KEY", "/root/.ssh/hetzner_key")


def get_servers() -> List[Dict]:
    """Get configured servers from environment."""
    servers_json = os.getenv("DOCKER_MONITOR_SERVERS", "").strip()
    try:
        parsed = json.loads(servers_json) if servers_json else []
        if isinstance(parsed, list):
            servers: List[Dict] = []
            for entry in parsed:
                if not isinstance(entry, dict):
                    continue
                host = str(entry.get("host", "")).strip()
                user = str(entry.get("user", "")).strip()
                if not host or not user:
                    continue
                port = int(entry.get("port", 22) or 22)
                aliases_raw = entry.get("aliases", [])
                aliases = (
                    [str(a).strip() for a in aliases_raw if str(a).strip()]
                    if isinstance(aliases_raw, list) else []
                )
                servers.append({
                    "name": str(entry.get("name", host)).strip() or host,
                    "host": host,
                    "user": user,
                    "port": port,
                    "aliases": aliases,
                })
            if servers:
                return servers
    except json.JSONDecodeError:
        pass

    # Legacy fallback: only when explicit single-host vars are configured
    host = os.getenv("DOCKER_MONITOR_HOST", "").strip()
    user = os.getenv("DOCKER_MONITOR_USER", "").strip()
    if host and user:
        port = int(os.getenv("DOCKER_MONITOR_PORT", "22"))
        return [{"name": host, "host": host, "user": user, "port": port}]

    return []


def _match_server(s: Dict, key: str) -> bool:
    """True wenn key den Server per Host, Name oder Alias (z. B. Public-IP) identifiziert."""
    return s["host"] == key or s.get("name") == key or key in s.get("aliases", [])


class SSHConnection:
    """Manage SSH connections to remote Docker host."""

    @staticmethod
    def execute(host: str, user: str, port: int, command: str) -> tuple[str, str, int]:
        """Execute command via SSH and return stdout, stderr, exit_code."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if os.path.exists(SSH_KEY_PATH):
                client.connect(
                    hostname=host,
                    port=port,
                    username=user,
                    key_filename=SSH_KEY_PATH,
                    timeout=10
                )
            else:
                raise FileNotFoundError(f"SSH key not found: {SSH_KEY_PATH}")

            stdin, stdout, stderr = client.exec_command(command, timeout=30)
            exit_code = stdout.channel.recv_exit_status()

            return stdout.read().decode(), stderr.read().decode(), exit_code
        finally:
            client.close()


@router.get("/servers")
async def list_monitored_servers():
    """List all configured servers for Docker monitoring."""
    servers = get_servers()
    result = []

    for server in servers:
        try:
            cmd = 'docker --version'
            stdout, stderr, exit_code = await asyncio.to_thread(
                SSHConnection.execute,
                server["host"], server["user"], server.get("port", 22), cmd
            )
            result.append({
                "name": server.get("name", server["host"]),
                "host": server["host"],
                "user": server["user"],
                "port": server.get("port", 22),
                "status": "connected" if exit_code == 0 else "error",
                "docker_version": stdout.strip() if exit_code == 0 else None,
                "error": stderr if exit_code != 0 else None
            })
        except Exception as e:
            result.append({
                "name": server.get("name", server["host"]),
                "host": server["host"],
                "user": server["user"],
                "port": server.get("port", 22),
                "status": "disconnected",
                "docker_version": None,
                "error": str(e)
            })

    return {"success": True, "servers": result}


@router.get("/containers")
async def list_containers(server: Optional[str] = Query(None, description="Server host/name")):
    """List all Docker containers on remote server with project grouping."""
    servers = get_servers()

    # Find server by host or name
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        # Extended format with project label and networks
        cmd = """docker ps -a --format '{"id":"{{.ID}}","name":"{{.Names}}","image":"{{.Image}}","status":"{{.Status}}","state":"{{.State}}","ports":"{{.Ports}}","created":"{{.CreatedAt}}","project":"{{.Label "com.docker.compose.project"}}","networks":"{{.Networks}}"}'"""
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        if exit_code != 0:
            raise HTTPException(status_code=500, detail=f"Docker command failed: {stderr}")

        containers = []
        for line in stdout.strip().split('\n'):
            if line:
                try:
                    container = json.loads(line)
                    state = container.get('state', '').lower()
                    container['running'] = state == 'running'
                    container['health'] = 'healthy' if state == 'running' else 'stopped'
                    containers.append(container)
                except json.JSONDecodeError:
                    continue

        return {
            "success": True,
            "server": target.get("name", target["host"]),
            "host": target["host"],
            "container_count": len(containers),
            "running_count": sum(1 for c in containers if c['running']),
            "containers": containers
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSH connection failed: {str(e)}")


@router.get("/containers/{container_name}/stats")
async def get_container_stats(container_name: str, server: Optional[str] = Query(None)):
    """Get resource stats for a specific container."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        cmd = f'docker stats {container_name} --no-stream --format \'{{"cpu":"{{{{.CPUPerc}}}}","memory":"{{{{.MemUsage}}}}","mem_perc":"{{{{.MemPerc}}}}","net_io":"{{{{.NetIO}}}}","block_io":"{{{{.BlockIO}}}}"}}\''
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        if exit_code != 0:
            raise HTTPException(status_code=404, detail=f"Container not found or not running: {container_name}")

        stats = json.loads(stdout.strip())
        return {
            "success": True,
            "server": target["host"],
            "container": container_name,
            "stats": stats
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse container stats")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/containers/{container_name}/logs")
async def get_container_logs(container_name: str, lines: int = 100, server: Optional[str] = Query(None)):
    """Get recent logs from a container."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        cmd = f'docker logs {container_name} --tail {lines} 2>&1'
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        if exit_code != 0 and "No such container" in stderr:
            raise HTTPException(status_code=404, detail=f"Container not found: {container_name}")

        return {
            "success": True,
            "server": target["host"],
            "container": container_name,
            "lines": lines,
            "logs": stdout
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/containers/{container_name}/restart")
async def restart_container(container_name: str, server: Optional[str] = Query(None)):
    """Restart a container."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        cmd = f'docker restart {container_name}'
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        if exit_code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to restart: {stderr}")

        return {
            "success": True,
            "message": f"Container {container_name} restarted",
            "server": target["host"],
            "container": container_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/containers/{container_name}/stop")
async def stop_container(container_name: str, server: Optional[str] = Query(None)):
    """Stop a container."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        cmd = f'docker stop {container_name}'
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        if exit_code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to stop: {stderr}")

        return {
            "success": True,
            "message": f"Container {container_name} stopped",
            "server": target["host"],
            "container": container_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/containers/{container_name}/start")
async def start_container(container_name: str, server: Optional[str] = Query(None)):
    """Start a stopped container."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        cmd = f'docker start {container_name}'
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        if exit_code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to start: {stderr}")

        return {
            "success": True,
            "message": f"Container {container_name} started",
            "server": target["host"],
            "container": container_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system")
async def get_system_info(server: Optional[str] = Query(None)):
    """Get Docker system information."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        cmd = 'docker system df --format \'{"type":"{{.Type}}","total":"{{.TotalCount}}","active":"{{.Active}}","size":"{{.Size}}","reclaimable":"{{.Reclaimable}}"}\''
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        if exit_code != 0:
            raise HTTPException(status_code=500, detail=f"Docker command failed: {stderr}")

        disk_usage = []
        for line in stdout.strip().split('\n'):
            if line:
                try:
                    disk_usage.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        version_cmd = 'docker version --format \'{"server":"{{.Server.Version}}","api":"{{.Server.APIVersion}}"}\''
        version_stdout, _, _ = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), version_cmd
        )
        version = json.loads(version_stdout.strip()) if version_stdout.strip() else {}

        return {
            "success": True,
            "server": target.get("name", target["host"]),
            "host": target["host"],
            "docker_version": version,
            "disk_usage": disk_usage
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disk-analysis")
async def get_disk_analysis(server: Optional[str] = Query(None)):
    """Analyze disk usage - get top directories and cleanup suggestions."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        # Get top directories by size
        cmd = '''
echo "=== TOP_DIRS ==="
du -h --max-depth=2 / 2>/dev/null | sort -hr | head -20

echo "=== DOCKER_USAGE ==="
docker system df 2>/dev/null || echo "Docker not available"

echo "=== DOCKER_VOLUMES ==="
docker system df -v 2>/dev/null | grep -A 100 "VOLUME NAME" | head -15 || echo "No volumes"

echo "=== DOCKER_IMAGES ==="
docker images --format "{{.Repository}}:{{.Tag}}\t{{.Size}}" 2>/dev/null | head -10 || echo "No images"

echo "=== LOG_FILES ==="
find /var/log -type f -name "*.log" -exec du -h {} + 2>/dev/null | sort -hr | head -10

echo "=== JOURNAL_SIZE ==="
journalctl --disk-usage 2>/dev/null || echo "N/A"

echo "=== OLD_CONTAINERS ==="
docker ps -a --filter "status=exited" --format "{{.Names}}\t{{.Status}}\t{{.Size}}" 2>/dev/null | head -10

echo "=== DANGLING_IMAGES ==="
docker images -f "dangling=true" --format "{{.ID}}\t{{.Size}}" 2>/dev/null | head -10

echo "=== APT_CACHE ==="
du -sh /var/cache/apt/archives 2>/dev/null || echo "0"
'''
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        # Parse results
        sections = {}
        current_section = None
        current_content = []

        for line in stdout.split('\n'):
            if line.startswith('=== ') and line.endswith(' ==='):
                if current_section:
                    sections[current_section] = current_content
                current_section = line.replace('=== ', '').replace(' ===', '')
                current_content = []
            elif current_section and line.strip():
                current_content.append(line)

        if current_section:
            sections[current_section] = current_content

        # Parse top directories
        top_dirs = []
        for line in sections.get('TOP_DIRS', []):
            parts = line.split('\t')
            if len(parts) >= 2:
                size, path = parts[0].strip(), parts[1].strip()
                if path and not path.startswith('/proc') and not path.startswith('/sys'):
                    top_dirs.append({"path": path, "size": size})

        # Parse Docker usage
        docker_usage = []
        for line in sections.get('DOCKER_USAGE', []):
            if line and not line.startswith('TYPE') and not line.startswith('Docker'):
                parts = line.split()
                if len(parts) >= 4:
                    docker_usage.append({
                        "type": parts[0],
                        "total": parts[1],
                        "active": parts[2],
                        "size": parts[3],
                        "reclaimable": parts[4] if len(parts) > 4 else "0B"
                    })

        # Parse log files
        log_files = []
        for line in sections.get('LOG_FILES', []):
            parts = line.split('\t')
            if len(parts) >= 2:
                log_files.append({"size": parts[0].strip(), "path": parts[1].strip()})

        # Parse old containers
        old_containers = []
        for line in sections.get('OLD_CONTAINERS', []):
            parts = line.split('\t')
            if len(parts) >= 2:
                old_containers.append({
                    "name": parts[0].strip(),
                    "status": parts[1].strip() if len(parts) > 1 else "",
                    "size": parts[2].strip() if len(parts) > 2 else "0B"
                })

        # Parse dangling images
        dangling_images = []
        for line in sections.get('DANGLING_IMAGES', []):
            parts = line.split('\t')
            if len(parts) >= 2:
                dangling_images.append({"id": parts[0].strip(), "size": parts[1].strip()})

        # Journal size
        journal_size = "N/A"
        for line in sections.get('JOURNAL_SIZE', []):
            if 'Archived and active journals' in line or 'take up' in line:
                journal_size = line.split(':')[-1].strip() if ':' in line else line

        # APT cache
        apt_cache = "0"
        for line in sections.get('APT_CACHE', []):
            if line:
                apt_cache = line.split()[0] if line.split() else "0"

        # Generate cleanup suggestions
        cleanup_suggestions = []

        # Docker cleanup suggestions
        for item in docker_usage:
            if item.get('reclaimable') and item['reclaimable'] != '0B':
                # Map type to correct command
                cmd_map = {
                    'Images': 'docker image prune -a',
                    'Containers': 'docker container prune',
                    'Local': 'docker volume prune',
                    'Build': 'docker builder prune',
                    'Volumes': 'docker volume prune'
                }
                cmd = cmd_map.get(item['type'], 'docker system prune')
                cleanup_suggestions.append({
                    "category": "Docker",
                    "description": f"Docker {item['type']} bereinigen",
                    "potential_savings": item['reclaimable'],
                    "command": cmd,
                    "risk": "medium" if item['type'] == 'Images' else "low",
                    "safe_for_production": item['type'] != 'Volumes'
                })

        # Old containers
        if old_containers:
            cleanup_suggestions.append({
                "category": "Docker",
                "description": f"{len(old_containers)} gestoppte Container entfernen",
                "potential_savings": "Variabel",
                "command": "docker container prune",
                "risk": "low",
                "safe_for_production": True
            })

        # Dangling images
        if dangling_images:
            total_dangling = len(dangling_images)
            cleanup_suggestions.append({
                "category": "Docker",
                "description": f"{total_dangling} ungenutzte Docker Images entfernen",
                "potential_savings": "Variabel",
                "command": "docker image prune",
                "risk": "low",
                "safe_for_production": True
            })

        # Journal logs
        if journal_size and journal_size != 'N/A' and 'M' in journal_size or 'G' in journal_size:
            cleanup_suggestions.append({
                "category": "System Logs",
                "description": "Systemd Journal Logs bereinigen",
                "potential_savings": journal_size,
                "command": "journalctl --vacuum-time=7d",
                "risk": "low",
                "safe_for_production": True
            })

        # APT cache
        if apt_cache and apt_cache not in ['0', '0B']:
            cleanup_suggestions.append({
                "category": "System",
                "description": "APT Paket-Cache leeren",
                "potential_savings": apt_cache,
                "command": "apt-get clean",
                "risk": "low",
                "safe_for_production": True
            })

        # Log files
        if log_files:
            cleanup_suggestions.append({
                "category": "Log Files",
                "description": "Alte Log-Dateien rotieren/löschen",
                "potential_savings": log_files[0]['size'] if log_files else "0",
                "command": "logrotate -f /etc/logrotate.conf",
                "risk": "low",
                "safe_for_production": True
            })

        return {
            "success": True,
            "server": target.get("name", target["host"]),
            "host": target["host"],
            "analysis": {
                "top_directories": top_dirs[:15],
                "docker_usage": docker_usage,
                "log_files": log_files[:10],
                "old_containers": old_containers,
                "dangling_images": dangling_images,
                "journal_size": journal_size,
                "apt_cache": apt_cache
            },
            "cleanup_suggestions": cleanup_suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def execute_cleanup(request: CleanupRequest, server: Optional[str] = Query(None)):
    """Execute a cleanup command on the server."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    command = request.command

    # Whitelist of safe cleanup commands
    safe_commands = [
        "docker system prune -f",
        "docker container prune -f",
        "docker image prune -f",
        "docker image prune -a -f",
        "docker volume prune -f",
        "docker builder prune -f",
        "journalctl --vacuum-time=7d",
        "journalctl --vacuum-size=500M",
        "apt-get clean",
        "apt-get autoremove -y",
    ]

    if command not in safe_commands:
        raise HTTPException(status_code=403, detail=f"Command not in whitelist: {command}")

    try:
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), command
        )

        return {
            "success": exit_code == 0,
            "command": command,
            "output": stdout,
            "error": stderr if exit_code != 0 else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-metrics")
async def get_system_metrics(server: Optional[str] = Query(None)):
    """Get live system metrics from server via SSH."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        # Collect multiple metrics in one SSH command
        cmd = '''
echo "CPU_PERCENT:$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)"
echo "MEMORY:$(free -m | awk 'NR==2{printf "%d %d %.1f", $3, $2, $3*100/$2}')"
echo "DISK:$(df -BG / | awk 'NR==2{gsub("G",""); printf "%d %d %.1f", $3, $2, $5}')"
echo "LOAD:$(cat /proc/loadavg | awk '{print $1, $2, $3}')"
echo "UPTIME:$(uptime -p | sed 's/up //')"
echo "NETWORK:$(cat /proc/net/dev | grep eth0 | awk '{print $2, $10}')"
echo "PROCESSES:$(ps aux | wc -l)"
'''
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        if exit_code != 0:
            raise HTTPException(status_code=500, detail=f"Command failed: {stderr}")

        # Parse results
        metrics = {}
        for line in stdout.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metrics[key.strip()] = value.strip()

        # Parse CPU
        cpu_percent = float(metrics.get('CPU_PERCENT', '0') or '0')

        # Parse Memory (used_mb total_mb percent)
        mem_parts = metrics.get('MEMORY', '0 0 0').split()
        memory_used = int(mem_parts[0]) if len(mem_parts) > 0 else 0
        memory_total = int(mem_parts[1]) if len(mem_parts) > 1 else 0
        memory_percent = float(mem_parts[2]) if len(mem_parts) > 2 else 0

        # Parse Disk (used_gb total_gb percent)
        disk_parts = metrics.get('DISK', '0 0 0').split()
        disk_used = int(disk_parts[0]) if len(disk_parts) > 0 else 0
        disk_total = int(disk_parts[1]) if len(disk_parts) > 1 else 0
        disk_percent = float(disk_parts[2]) if len(disk_parts) > 2 else 0

        # Parse Load
        load_parts = metrics.get('LOAD', '0 0 0').split()
        load_1 = float(load_parts[0]) if len(load_parts) > 0 else 0
        load_5 = float(load_parts[1]) if len(load_parts) > 1 else 0
        load_15 = float(load_parts[2]) if len(load_parts) > 2 else 0

        # Parse Network (rx_bytes tx_bytes)
        net_parts = metrics.get('NETWORK', '0 0').split()
        network_rx = int(net_parts[0]) if len(net_parts) > 0 else 0
        network_tx = int(net_parts[1]) if len(net_parts) > 1 else 0

        # Processes
        processes = int(metrics.get('PROCESSES', '0') or '0')

        return {
            "success": True,
            "server": target.get("name", target["host"]),
            "host": target["host"],
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_used": memory_used,
                "memory_total": memory_total,
                "memory_percent": memory_percent,
                "disk_used": disk_used,
                "disk_total": disk_total,
                "disk_percent": disk_percent,
                "load_1": load_1,
                "load_5": load_5,
                "load_15": load_15,
                "uptime": metrics.get('UPTIME', 'N/A'),
                "network_rx": network_rx,
                "network_tx": network_tx,
                "processes": processes
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_connection(server: Optional[str] = Query(None)):
    """Check SSH connection to Docker host."""
    servers = get_servers()
    target = None
    if server:
        for s in servers:
            if _match_server(s, server):
                target = s
                break
    else:
        target = servers[0] if servers else None

    if not target:
        return {
            "success": False,
            "status": "no_servers",
            "error": "No servers configured"
        }

    try:
        cmd = 'echo "ok" && docker --version'
        stdout, stderr, exit_code = await asyncio.to_thread(
            SSHConnection.execute,
            target["host"], target["user"], target.get("port", 22), cmd
        )

        if exit_code == 0:
            return {
                "success": True,
                "server": target.get("name", target["host"]),
                "host": target["host"],
                "status": "connected",
                "docker": stdout.strip().split('\n')[-1] if stdout else "unknown"
            }
        else:
            return {
                "success": False,
                "server": target.get("name", target["host"]),
                "host": target["host"],
                "status": "error",
                "error": stderr
            }
    except Exception as e:
        return {
            "success": False,
            "server": target.get("name", target["host"]) if target else "unknown",
            "host": target["host"] if target else "unknown",
            "status": "disconnected",
            "error": str(e)
        }
