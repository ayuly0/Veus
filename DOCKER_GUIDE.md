# Veus: Docker & Podman Setup Guide

This guide provides instructions for setting up and running Veus using a containerized environment (Alpine Linux). This is the recommended way to run Veus as it ensures all dependencies (including the Lua scripting engine) are correctly compiled and isolated.

## Prerequisites

- **Docker** OR **Podman** installed on your system.
- (Optional) **docker-compose** or **podman-compose**.

---

## 🚀 Quick Start (Recommended)

The easiest way to run Veus is using the provided `docker-compose.yml`. It handles the interactive terminal (TTY) and volume mounting automatically.

### 1. Configure your files
Ensure you have your tokens in `tokens.txt` and any Lua scripts in the `scripts/` directory.

### 2. Run the Container

**Using Docker Compose:**
```bash
docker-compose up --build
```

**Using Podman Compose:**
```bash
podman-compose up --build
```

---

## 🛠️ Manual Setup (Without Compose)

If you prefer using raw commands, follow these steps:

### 1. Build the Image
```bash
# Docker
docker build -t veus .

# Podman
podman build -t veus .
```

### 2. Run Interactively
Veus requires an interactive TUI. You **must** use the `-it` flags.

**Docker:**
```bash
docker run -it --rm \
  -v ./scripts:/app/scripts \
  -v ./tokens.txt:/app/tokens.txt \
  veus
```

**Podman (with SELinux support):**
```bash
podman run -it --rm \
  -v ./scripts:/app/scripts:z \
  -v ./tokens.txt:/app/tokens.txt:z \
  veus
```

---

## 💡 Troubleshooting (Alpine-Specific)

- **Input Lag**: If the TUI feels slow, ensure your terminal emulator supports high-frequency updates (e.g., Alacritty, Kitty, or modern GNOME Terminal).
- **Volume Permissions**: If using Podman, the `:z` flag is essential for SELinux systems (Fedora, RHEL, etc.) to allow the container to read your local files.
- **Scripting Error**: If Lua scripts fail to load, ensure they are placed in the `scripts/` directory before starting the container.
