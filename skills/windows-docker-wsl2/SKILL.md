---
name: windows-docker-wsl2
description: Control Windows Docker Desktop from WSL2. Use when needing to list, start, stop, inspect, or manage containers and images on the Windows Docker host. Handles the WSL2-to-Windows Docker daemon connection (DOCKER_HOST + docker.exe path).
---

# Windows Docker from WSL2

## Connection Setup

Windows Docker Desktop exposes its daemon on TCP port `2375`. From WSL2, connect by setting `DOCKER_HOST` and using the Windows docker executable path.

**Always use both:**
```bash
export DOCKER_HOST="tcp://localhost:2375"
docker="/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"
```

**Full command prefix (use in every exec call):**
```bash
DOCKER_HOST="tcp://localhost:2375" /mnt/c/Program\ Files/Docker/Docker/resources/bin/docker.exe <command>
```

## Quick Verification

```bash
curl -s --connect-timeout 3 http://localhost:2375/version
```

## Common Commands

```bash
# List running containers
DOCKER_HOST="tcp://localhost:2375" /mnt/c/Program\ Files/Docker/Docker/resources/bin/docker.exe ps

# List all containers (including stopped)
DOCKER_HOST="tcp://localhost:2375" /mnt/c/Program\ Files/Docker/Docker/resources/bin/docker.exe ps -a

# View container logs
DOCKER_HOST="tcp://localhost:2375" /mnt/c/Program\ Files/Docker/Docker/resources/bin/docker.exe logs <container_name>

# Stop / start a container
DOCKER_HOST="tcp://localhost:2375" /mnt/c/Program\ Files/Docker/Docker/resources/bin/docker.exe stop <container_name>
DOCKER_HOST="tcp://localhost:2375" /mnt/c/Program\ Files/Docker/Docker/resources/bin/docker.exe start <container_name>

# Inspect a container
DOCKER_HOST="tcp://localhost:2375" /mnt/c/Program\ Files/Docker/Docker/resources/bin/docker.exe inspect <container_name>

# List images
DOCKER_HOST="tcp://localhost:2375" /mnt/c/Program\ Files/Docker/Docker/resources/bin/docker.exe images
```

## Known Issues

- `/usr/bin/docker` symlink in WSL2 may be broken (points to `cli-tools` that don't exist). Always use the Windows `docker.exe` path directly.
- `localhost:2375` resolves from WSL2 to the Windows host correctly via WSL2's integrated networking.
