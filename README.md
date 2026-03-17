<a name="readme-top"></a>

<div align="center">
  <h1 align="center">Veus</h1>
  <p align="center">
    <strong>The Senior Discord Experience</strong>
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

Veus (v1) transforms your Discord interaction into a professional terminal shell. Built with a senior-tier asynchronous architecture, it focuses on performance, security, and visual excellence.

### Key Highlights

- **High-Performance Startup**: Parallelized synchronization of profile and server data.
- **Bulletproof ID Resolution**: Smart 4-digit shortcuts with interactive collision handling.
- **Windowed Fetching**: Professional pagination with older/newer scrolling and targeted jumps.
- **Senior Proxy System**: Round-robin and Random rotation with automatic health tracking and SSL bypass.
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

### Quick Config
- **tokens.txt**: Place your Discord tokens (one per line) for use with the **Identity Vault**.
- **proxies.txt**: Add your proxies (formatted as `http://user:pass@host:port`) for the **Secure Tunnel**.

---

## Senior Command Suite

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

## Security & Privacy
- **Zero-Storage**: Tokens are never stored in plain-text config files.
- **Secure Tunneling**: Full support for SSL bypass and custom proxy rotations.
- **Ephemeral Sessions**: Designed to be clean and leave no trace on exit.
- **Silent Network**: Intelligent caching to reduce unnecessary API telemetry.

---

## License
Distributed under the GPL-3.0 License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
