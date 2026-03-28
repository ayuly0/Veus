<a name="readme-top"></a>

<div align="center">
  <h1 align="center">Veus</h1>
  <p align="center">
    <strong>The Terminal Shell Experience</strong>
    <br />
    A minimalist, high-performance Discord terminal controller and shell.
    <br />
    <a href="https://github.com/ayuly0/veus/issues">Report Bug</a>
    ·
    <a href="https://github.com/ayuly0/veus/issues">Request Feature</a>
  </p>
</div>

---

## The Experience

Veus (v1) transforms your Discord interaction into a terminal shell. Built with a asynchronous architecture, it focuses on performance, security, and visual excellence.

### Key Highlights

- **High-Performance Startup**: Parallelized synchronization of profile and server data.
- **Bulletproof ID Resolution**: Smart 4-digit shortcuts with interactive collision handling.
- **Windowed Fetching**: Pagination with older/newer scrolling and targeted jumps.
- **Proxy System**: Round-robin and Random rotation with automatic health tracking and SSL bypass.
- **The Landing Zone**: A unified, high-impact session initiation menu (Direct, Proxy, or Vault).
- **Deep Message Inspection**: Full context retrieval for any message ID (Direct + Fallback).

---

## Getting Started

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/ayuly0/veus.git
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Launch the shell:
   ```sh
   python -m veus
   ```

### 🐳 Containerized Setup (Docker / Podman)

For a secure, pre-configured environment (recommended), see the **[Docker Setup Guide](DOCKER_GUIDE.md)**.

```sh
# Quick Start (Podman)
podman-compose up --build
```

### Configuration & Secrets

Veus supports secure secret management via environment variables.

1. **.env Configuration (Recommended)**:
   Copy `.env.example` to `.env` and fill in your details:
   ```sh
   DISCORD_TOKEN=your_token_here
   DISCORD_IS_BOT=false
   ```
2. **Legacy Vault (Alternative)**:
   - **tokens.txt**: Place Discord tokens (one per line) for use with the **Identity Vault**. *Note: A security warning will trigger if this legacy method is used.*
   - **proxies.txt**: Add proxies (`http://user:pass@host:port`) for the **Secure Tunnel**.

---

## Command Suite

| Category | Primary Command | Aliases | Description |
| :--- | :--- | :--- | :--- |
| **Messaging** | `message` | `msg`, `send` | Send messages with interactive prompting. |
| | `fetch` | `ls`, `history` | Windowed history (older/newer/select). |
| | `reply` | `re` | Smart reply using 4-digit ID resolution. |
| | `inspect` | `view`, `v` | View deep context and attachment URLs. |
| | `dms` | | Focus on private/bot conversations. |
| **Guild** | `servers` | `sv`, `guilds` | List and select active guild context. |
| | `select` | `focus`, `use` | Focus on a channel or DM by ID. |
| | `channels` | `ch` | List channels (supports --refresh). |
| **Moderation** | `purge` | `p` | Mass delete messages in focused channel. |
| | `slowmode` | `sm` | Control channel rate limits instantly. |
| **Profile** | `profile` | `bio`, `me` | Update user bio and presence info. |
| | `status` | `presence` | Set online status (online, dnd, idle). |
| **General** | `help` | `h` | View this advanced help system. |
| | `exit` | `q`, `quit` | Graceful session termination. |

---

## Security & Hardening

Veus is built with a "Security-First" architecture to protect your identities:

- **Secret Management**: Support for `.env` and environment variables to prevent cleartext token exposure.
- **Hardened Sandbox**: Lua scripting engine is restricted to prevent Remote Code Execution (RCE).
- **Path Traversal Protection**: Secure path sanitization for all file downloads.
- **SSL-First Tunneling**: Mandatory SSL verification by default with high-impact warnings for insecure configurations.
- **Least-Privilege Docker**: Official images run as a non-root user (`veus-ops`) to prevent container escape.
- **Silent Telemetry**: Intelligent caching to reduce unnecessary API fingerprints.

---

## License
Distributed under the GPL-3.0 License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
