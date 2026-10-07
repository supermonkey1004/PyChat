# 💬 PyChat

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none%20·%20stdlib%20only-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-tkinter-ff69b4)
![Network](https://img.shields.io/badge/network-LAN%20auto--discovery-orange)

A self-contained **LAN chat room with a full admin control panel**, written in **pure Python with zero external libraries** — no `pip install`, ever. Start the server on one machine and clients on the same network discover it automatically. No IP addresses to type, no dependencies to manage.

---

## 📖 Overview

PyChat is two programs that talk to each other over your local network:

| | |
| --- | --- |
| 🖥️ **Server** (`server code.py`) | The host + admin control panel: activity log, connected-user list, moderation tools and a security audit log. |
| 💬 **Client** (`client code.py`) | The chat window each person connects with. |

They exchange length-framed **JSON packets over TCP**, and the server continuously beacons its location over **UDP** so clients can join with a single click.

---

## ✨ Features

### Chat & messaging
- **Global lobby chat** with per-message timestamps.
- **Markdown formatting** inline: `**bold**`, `*italic*`, `__underline__`, `~~strikethrough~~` and `` `code` ``.
- **Private direct messages** between users.
- **Automatic server discovery** over UDP — no manual IP entry.
- **Reconnect support** — rejoin and reclaim your name.
- **Spam & duplicate-message throttling**.

### Identity & usernames
- Approved display names live **on the server** and are downloaded by clients.
- Pick your name from a scrollable list at login; **names already in use are greyed out**.
- Change your name later from the same picker.
- The server sees each client's **real Windows username** and IP (shown on hover).

### File & image sharing
- Share **any file up to 20 MB**, delivered as a **clickable download link** in the chat.
- **Paste an image** straight from the clipboard with `Ctrl+V` or the *Paste Image* button (Windows).

### Moderation & safety
- **Content blocklist filter** with escalating on-screen warnings.
- **User reports** — at 5 reports the admin is prompted to **Kick / Shut Down PC / Dismiss**.
- **Timed mutes** and instant kicks.
- A dedicated **security audit log**.

### Admin control panel
Right-click any connected user for the full toolkit:

| Action | What it does |
| --- | --- |
| **Kick User** | Disconnects them from the chat |
| **Shut Down Client PC** | Sends a transparent shutdown command to their machine (with confirmation) |
| **Mute User** | Silences them for a set number of seconds |
| **Play Sound** | Triggers a beep/alarm on their device |
| **Send Fullscreen Overlay** | Pushes a searchable, grid-tileable text overlay |
| **Send Image Overlay** | Displays a chosen PNG/GIF fullscreen on their screen |
| **Web Link Redirect** | Opens a URL in their browser |

Plus a **broadcast terminal** for announcements to everyone at once.

### Security & integrity
- Optional **client integrity check** (`STRICT_HASH_CHECK`): the server can refuse any client whose file doesn't match an approved **SHA-256** hash — useful for blocking modified or outdated clients.
- `add_client_hash.py` registers approved client builds.

---

## ⚙️ Requirements

- **Python 3.x** — the only requirement. No third-party packages.
- **Windows** recommended. Sounds, clipboard image paste and the PC-shutdown feature use Windows-specific facilities; core chat works cross-platform.

---

## 🚀 Getting started

Clone or download the repository, then:

```bash
# 1. On the HOST machine — start the server
python "server code.py"

# 2. On each CLIENT machine (same network) — start the client
python "client code.py"
```

The client finds the server automatically, shows the approved-name picker, and drops you into the lobby. That's it.

> **Tip:** All machines must be on the same local network, and the firewall must allow TCP port **50002** and UDP port **50001**.

---

## 🔧 Configuration

Key settings live near the top of `server code.py`:

| Setting | Default | Purpose |
| --- | --- | --- |
| `CHAT_PORT` | `50002` | TCP port for chat traffic |
| `DISCOVERY_PORT` | `50001` | UDP port for server auto-discovery |
| `STRICT_HASH_CHECK` | `False` | When `True`, only approved client builds may connect |

Data files (created automatically if missing):

| File | Purpose |
| --- | --- |
| `chosen names/allowed names.txt` | Approved usernames, one per line (`#` lines are comments) |
| `blocklist.txt` | Filtered words, one per line |
| `allowed client hashes.txt` | SHA-256 hashes of approved client builds |

### Registering an approved client

```bash
python "add_client_hash.py" "client code.py" "a short description"
```

Run this after any change to `client code.py`, then set `STRICT_HASH_CHECK = True` to enforce it. (While you're still editing the client, leave the check off — every edit changes the hash.)

---

## 🗂️ Project structure

```
PyChat/
├── server code.py            # Server + admin control panel
├── client code.py            # Chat client
├── add_client_hash.py        # Registers approved client builds
├── chosen names/
│   └── allowed names.txt      # Approved usernames
├── blocklist.txt             # Filtered words
└── allowed client hashes.txt  # Approved client SHA-256 hashes
```

---

## 🧠 How it works

- **Transport:** every message is a JSON object prefixed with a 4-byte length header, sent over a TCP socket — so packets are always framed correctly even across multiple reads.
- **Discovery:** the server broadcasts `CHAT_SERVER <port>` over UDP every couple of seconds; the client listens for it and connects, so there's no IP address to configure.
- **Concurrency:** the server handles each client on its own thread, keeping the GUI responsive.
- **Admin commands:** the server sends typed packets (e.g. an overlay or shutdown command) to a specific client, which the client routes to the matching handler.

---

## ⚠️ Responsible use

PyChat includes admin features that act on a client's computer — remote shutdown, fullscreen overlays, sounds and browser redirects. These are intended for machines **you administer**, used **with the knowledge and consent** of the people on them (for example your own devices or a classroom/LAN group that has agreed to it). Every remote action is transparent: the client shows what is happening and nothing is hidden or persistent. Don't use these features against people who haven't agreed to run the client.

---

## 📝 Limitations

- tkinter can only display **PNG/GIF** without extra libraries, so pasted clipboard images are shared as downloadable `.bmp` attachments rather than shown inline.
- Sounds, clipboard paste and PC-shutdown are **Windows-only**.
- Designed for trusted local networks; traffic is not encrypted.

---

## 📄 License

No license has been chosen yet. Add one (for example [MIT](https://choosealicense.com/licenses/mit/)) if you want to let others reuse this code.
