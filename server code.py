# ==============================================================================
# CHAT SERVER CODE - CLEAN WHITE THEME & 100 MEME OVERLAYS (NO STATUSES)
# ==============================================================================

# Import built-in Python libraries (no extra installation needed!)
import socket      # Handles network connections (TCP/UDP)
import threading   # Allows the server to do multiple things at once (concurrency)
import time        # Handles timestamps, delays, and uptime tracking
import re          # Regular Expressions: used for searching and manipulating text
import os          # Interacts with the computer's operating system and file system
import struct      # Converts Python data types into structured binary bytes
import hashlib     # Cryptographic hashing: used here for client file verification
import unicodedata # Normalizes characters (e.g. converts accented text to plain text)
import json        # Converts Python dictionaries to/from structured text strings
import base64      # Encodes binary files (like images/docs) into safe text format
import tkinter as tk # Built-in GUI library for desktop applications
from tkinter import messagebox, simpledialog, ttk # GUI popup dialogs and modern widgets

# ------------------------------------------------------------------------------
# GLOBAL CONFIGURATION VARIABLES
# ------------------------------------------------------------------------------
CHAT_PORT = 50002       # The port used for sending and receiving chat messages (TCP)
DISCOVERY_PORT = 50001 # The port used to broadcast the server's location (UDP)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHOSEN_NAMES_FILE = os.path.join(BASE_DIR, "chosen names", "allowed names.txt")
ALLOWED_HASHES_FILE = os.path.join(BASE_DIR, "allowed client hashes.txt")

# Set this to True to block clients if their code has been altered or renamed.
# Set to False to allow any client connection regardless of file hash.
STRICT_HASH_CHECK = True

# Professional light theme color palette: pure white background with soft panels
BG_MAIN = "#FFFFFF"      # Clean white main background
BG_BOX = "#F5F7F8"       # Soft light-grey boxes/panels for widgets
FG_TEXT = "#1C1E21"      # Dark charcoal text for comfortable reading
ACCENT_BLUE = "#0066CC"  # Professional blue accents
ACCENT_RED = "#D32F2F"   # Warning/alert red
BORDER_COLOR = "#D0D0D0" # Crisp borders separating functional areas

clients = []           # Keeps track of all connected client dictionaries
displayed_clients = [] # Stores list of active clients currently rendered in the GUI
user_reports = []      # Log of reported policy/abuse incidents
FORBIDDEN_WORDS = []   # List of words loaded from the blocklist file
ALLOWED_NAME_OPTIONS = []

# ------------------------------------------------------------------------------
# PROGRAMMATIC GENERATION OF 100 MEMES (2019-2026) & EMOJIS
# ------------------------------------------------------------------------------
# Populating exactly 100 entries programmatically to prevent file truncation
PRANK_DATABASE = []

years = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
memes = [
    "Stonks Chart", "Area 51 Naruto Run", "Woman Yelling at Cat", "Surprised Pikachu",
    "Coffin Dance", "Trade Offer Deal", "GigaChad Jawline", "It's Corn!", "Grimace Shake Drips",
    "Chill Guy Posture", "Mewing Silence Gesture", "Demure Boundaries Grid", "Subway Splitscreen",
    "Brainrot Level Max", "Quantum CPU Grid Alert", "Neural Link Brain Wave", "End of Internet Warning"
]
emojis = [
    "Clown Face", "Suspicious Side-Eye", "Skull Face (Dead)", "Angry Red Face",
    "Sarcastic Eye-Roll", "Raised Eyebrow", "Palm Facepalm", "Sarcastic Salute",
    "Thinking Face", "Yawning Bored Face", "Shrugging Hand Pose", "Loud Crying Stream"
]

# Generate 80 historically accurate structured meme templates spanning 2019-2026
for i in range(1, 81):
    yr = years[(i - 1) % len(years)]
    m_name = memes[(i - 1) % len(memes)]
    PRANK_DATABASE.append({
        "id": f"meme_{yr}_{i}",
        "name": f"{m_name} ({yr}) - Style {i}",
        "desc": f"Famous procedural visual alert style from year {yr} (Variant #{i})"
    })

# Generate 20 highly expressive/suspicious emoji profiles
for i in range(1, 21):
    emo = emojis[(i - 1) % len(emojis)]
    PRANK_DATABASE.append({
        "id": f"emoji_{emo.lower().replace(' ', '_')}_{i}",
        "name": f"Sus {emo} - Variant {i}",
        "desc": f"Renders a high-contrast vector emoji face (Variant #{i})"
    })

# ------------------------------------------------------------------------------
# SECURITY INTEGRITY VERIFICATION
# ------------------------------------------------------------------------------
def get_expected_client_hash():
    """Computes unique SHA-256 fingerprint of client file with normalization."""
    candidate_paths = [
        os.path.join(BASE_DIR, "client code 2.py"),
        os.path.join(BASE_DIR, "client.py"),
    ]
    filename = next((path for path in candidate_paths if os.path.exists(path)), None)
    if not filename:
        return "DEFAULT_IDLE_CLIENT_TOKEN_v3.0"
    try:
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.rstrip() for line in normalized.split("\n")]
        normalized_content = "\n".join(lines).strip()
        return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
    except Exception:
        return "DEFAULT_IDLE_CLIENT_TOKEN_v3.0"



EXPECTED_HASH = get_expected_client_hash()

# ------------------------------------------------------------------------------
# CHAT CONTENT FILTER & NORMALIZATION
# ------------------------------------------------------------------------------
def load_forbidden_words(filename="blocklist.txt"):
    """Loads terms from a local text file to check for banned phrases."""
    global FORBIDDEN_WORDS
    loaded_words = []
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith("#"):
                        loaded_words.append(word)
            log_server_event(f"Loaded {len(loaded_words)} terms from '{filename}'.")
        except Exception as e:
            log_server_event(f"Error reading blocklist: {e}")
    else:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("# Blocklist File\noffensiveword1\n")
            loaded_words = ["offensiveword1"]
        except Exception as e:
            log_server_event(f"Could not generate template blocklist: {e}")
    FORBIDDEN_WORDS = loaded_words


def load_allowed_names(filename=CHOSEN_NAMES_FILE):
    """Loads approved display names from a text file."""
    global ALLOWED_NAME_OPTIONS
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    allowed_names = []
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    entry = line.strip()
                    if entry and not entry.startswith("#"):
                        allowed_names.append(entry)
        except Exception as e:
            log_server_event(f"Error reading allowed names: {e}")
    else:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("# One approved username per line\nUser\nGuest\nPlayer\n")
            allowed_names = ["User", "Guest", "Player"]
        except Exception as e:
            log_server_event(f"Could not generate allowed names file: {e}")
    ALLOWED_NAME_OPTIONS = allowed_names


def load_allowed_client_hashes(filename=ALLOWED_HASHES_FILE):
    """Loads approved client hashes from the hash registry file."""
    hashes = set()
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    entry = line.strip()
                    if entry and not entry.startswith("#"):
                        hashes.add(entry.split()[0])
        except Exception as e:
            log_server_event(f"Error reading allowed hashes: {e}")
    return hashes


def name_is_available(candidate_name, exclude_client=None):
    """Checks whether a display name is allowed and not already in use."""
    requested = candidate_name.strip()
    if not requested:
        return False, "empty"

    if ALLOWED_NAME_OPTIONS:
        allowed = {item.lower() for item in ALLOWED_NAME_OPTIONS}
        if requested.lower() not in allowed:
            return False, "not_allowed"

    for client in clients:
        if client is exclude_client:
            continue
        if client["status"] != "offline" and client["name"].lower() == requested.lower():
            return False, "taken"

    return True, "ok"


def advanced_normalize(text):
    """Normalizes text to detect bypassed filter words (e.g. 'L00k' -> 'look')."""
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    normalized = normalized.lower()
    normalized = re.sub(r'[\u200b-\u200d\ufeff]', '', normalized)
    
    substitutions = {
        '0': 'o', '1': 'i', '2': 'z', '3': 'e', '4': 'a', 
        '5': 's', '7': 't', '8': 'b', '9': 'g', '@': 'a', 
        '$': 's', '!': 'i', 'v': 'u', 'w': 'uu', '\\/': 'v'
    }
    for pattern, replacement in substitutions.items():
        normalized = normalized.replace(pattern, replacement)
        
    clean_text = "".join(c for c in normalized if c.isalnum())
    if clean_text:
        collapsed = [clean_text[0]]
        for char in clean_text[1:]:
            if char != collapsed[-1]:
                collapsed.append(char)
        clean_text = "".join(collapsed)
    return clean_text


def contains_forbidden_words(message):
    """Checks if any bad words are hidden inside the message."""
    normalized_message = advanced_normalize(message)
    for word in FORBIDDEN_WORDS:
        normalized_target = advanced_normalize(word)
        if normalized_target in normalized_message:
            return True
    return False

# ------------------------------------------------------------------------------
# PACKET TRANSMISSION (TCP FRAMEWORK)
# ------------------------------------------------------------------------------
def send_packet(sock, data_dict):
    """Sends JSON-serialized dictionary packets over TCP."""
    try:
        data = json.dumps(data_dict).encode("utf-8")
        header = struct.pack("!I", len(data))
        sock.sendall(header + data)
    except Exception:
        pass


def recv_packet(sock):
    """Receives JSON-serialized dictionary packets."""
    try:
        header = recv_all(sock, 4)
        if not header:
            return None
        length = struct.unpack("!I", header)[0]
        data = recv_all(sock, length)
        if not data:
            return None
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None


def recv_all(sock, length):
    """Helper method to guarantee reading exactly 'length' bytes from a TCP stream."""
    data = bytearray()
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

# ------------------------------------------------------------------------------
# BROADCASTS & STATE LIFECYCLE
# ------------------------------------------------------------------------------
def broadcast_presence():
    """Broadcasts UDP packets so clients can discover the server automatically."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message = f"CHAT_SERVER {CHAT_PORT}".encode()
    while True:
        try:
            udp_socket.sendto(message, ("255.255.255.255", DISCOVERY_PORT))
            time.sleep(2)
        except Exception:
            break


def broadcast_global(packet):
    """Sends a packet to every active, online connected client."""
    for client in list(clients):
        if client["status"] != "offline" and client["socket"]:
            send_packet(client["socket"], packet)


def update_user_lists():
    """Tells all clients to refresh their list of connected users."""
    for client in list(clients):
        if client["status"] != "offline" and client["socket"]:
            members = [
                {
                    "name": c["name"],
                    "previous_names": list(c.get("name_history", []))
                }
                for c in clients
                if c["status"] != "offline"
            ]
            send_packet(client["socket"], {
                "type": "user_list_update",
                "members": members
            })


def remove_client(client):
    """Safely disconnects clients. Protects against Tkinter threading crashes."""
    if client in clients:
        if client["socket"]:
            try:
                client["socket"].close()
            except Exception:
                pass
            client["socket"] = None
        client["disconnect_time"] = time.time()
        
        exit_reason = client.get("kicked")
        if exit_reason == "admin":
            client["status"] = "offline"
            log_server_event(f"* {client['name']} disconnected (kicked by admin)")
            broadcast_global({
                "type": "system",
                "content": f"[SYSTEM] {client['name']} has been kicked by an administrator.\n"
            })
        elif exit_reason == "policy":
            client["status"] = "offline"
            log_server_event(f"* {client['name']} disconnected (policy violation)")
            broadcast_global({
                "type": "system",
                "content": f"[SYSTEM] {client['name']} has been removed for policy violations.\n"
            })
        elif exit_reason == "shutdown":
            client["status"] = "offline"
            log_server_event(f"* {client['name']} disconnected (server shutdown)")
        else:
            client["status"] = "offline"
            log_server_event(f"* {client['name']} disconnected (left chat)")
            broadcast_global({
                "type": "system",
                "content": f"[LEFT] {client['name']} left the server.\n"
            })
            
        update_user_lists()
        # Thread safety guard check to bypass command registration on dead window loops
        try:
            if window.winfo_exists():
                window.after(0, update_client_list_gui)
        except Exception:
            pass


def handle_client(client_socket, address):
    """Main thread handler for each individual connected client socket."""
    handshake = recv_packet(client_socket)
    if not handshake or handshake.get("type") != "handshake":
        client_socket.close()
        return

    load_allowed_names()
    allowed_hashes = load_allowed_client_hashes()

    client_hash = handshake.get("hash", "")
    if not allowed_hashes:
        log_server_event("[WARNING] No approved client hashes found in allowed client hashes.txt.")
    if STRICT_HASH_CHECK:
        if allowed_hashes and client_hash not in allowed_hashes:
            log_server_event(f"[SECURITY] Rejected connection at {address[0]} - client hash not approved.")
            send_packet(client_socket, {"type": "reject_integrity", "reason": "client_not_approved"})
            client_socket.close()
            return
    else:
        if allowed_hashes and client_hash not in allowed_hashes:
            log_server_event(f"[INFO] Hash mismatch from {address[0]} (ignored — STRICT_HASH_CHECK is off).")

    name = handshake.get("name", "Unknown").strip()

    # Reject empty or whitespace-only names during registration handshake
    if not name:
        log_server_event(f"[SECURITY] Rejected connection at {address[0]} - Handshake contains empty name.")
        send_packet(client_socket, {"type": "name_rejected", "reason": "empty"})
        client_socket.close()
        return

    if contains_forbidden_words(name):
        log_server_event(f"[MODERATION] Blocked registration - Offensive name: '{name}'")
        send_packet(client_socket, {"type": "name_rejected", "reason": "blocked"})
        client_socket.close()
        return

    is_available, reason = name_is_available(name)
    if not is_available:
        log_server_event(f"[SECURITY] Rejected connection at {address[0]} - name '{name}' unavailable ({reason}).")
        send_packet(client_socket, {"type": "name_taken", "name": name, "reason": reason, "allowed": ALLOWED_NAME_OPTIONS})
        client_socket.close()
        return

    send_packet(client_socket, {"type": "handshake_ok"})

    client = None
    for old_client in clients:
        if old_client["name"].lower() == name.lower() and old_client["status"] == "offline":
            client = old_client
            client["socket"] = client_socket
            client["status"] = "online"
            client["disconnect_time"] = None
            client["kicked"] = None
            log_server_event(f"* {name} reconnected from {address[0]}")
            broadcast_global({
                "type": "system",
                "content": f"[RECONNECT] {name} reconnected to the server.\n"
            })
            break

    if not client:
        client = {
            "socket": client_socket,
            "name": name,
            "addr": address,
            "kicked": None,
            "status": "online",
            "disconnect_time": None,
            "group": "general",
            "mute_until": 0,
            "name_history": [],
            "message_history": [],
            "report_flags": 0,       # Track reports received (Confirm boot on 6)
            "blocklist_flags": 0     # Track blocklist triggers (Autoboot on 3)
        }
        clients.append(client)
        log_server_event(f"* {name} joined from {address[0]}")
        broadcast_global({
            "type": "system",
            "content": f"[JOIN] {name} has joined the chat.\n"
        })
    update_user_lists()
    
    try:
        if window.winfo_exists():
            window.after(0, update_client_list_gui)
    except Exception:
        pass

    while True:
        packet = recv_packet(client_socket)
        if packet is None:
            break
        
        packet_type = packet.get("type")
        current_time = time.time()
        allowed_packet_types = {"message", "dm", "name_change", "report", "file_share"}
        if packet_type not in allowed_packet_types:
            log_server_event(f"[SECURITY] Rejected unexpected packet type from @{client['name']}: {packet_type}")
            send_packet(client_socket, {
                "type": "system",
                "content": "[SECURITY] Unsupported client packet was rejected.\n"
            })
            continue

        if packet_type == "message":
            if current_time < client.get("mute_until", 0):
                remaining = int(client["mute_until"] - current_time)
                send_packet(client_socket, {
                    "type": "system",
                    "content": f"[MUTED] You are currently muted. Remaining: {remaining}s.\n"
                })
                continue

            content = packet.get("content", "").strip()
            
            # --- Automated Blocklist Warning/Boot Handling ---
            if contains_forbidden_words(content):
                client["blocklist_flags"] += 1
                log_server_event(f"[MODERATION] Filter word triggered by @{client['name']} ({client['blocklist_flags']}/3)")
                
                if client["blocklist_flags"] >= 3:
                    # Automatically boot on 3rd violation
                    client["kicked"] = "policy"
                    send_packet(client_socket, {"type": "kicked_policy"})
                    log_server_event(f"[MODERATION] Auto-booted @{client['name']} for reaching 3 blocklist flags.")
                    break
                else:
                    # Warn on 1st and 2nd violation
                    send_packet(client_socket, {
                        "type": "system",
                        "content": f"⚠️ SYSTEM WARNING: Your message triggered the content filter. This is flag {client['blocklist_flags']}/3. Reaching 3 will result in an automated boot.\n"
                    })
                    continue

            client["message_history"] = [
                (t, msg) for t, msg in client["message_history"] 
                if current_time - t <= 60
            ]
            duplicate_count = sum(1 for t, msg in client["message_history"] if msg == content)
            if duplicate_count >= 3:
                send_packet(client_socket, {
                    "type": "system",
                    "content": "[WARNING] Slow down! Don't spam messages.\n"
                })
                continue
            
            client["message_history"].append((current_time, content))
            
            broadcast_global({
                "type": "message",
                "sender": client["name"],
                "content": content
            })

        elif packet_type == "dm":
            target_name = packet.get("target")
            content = packet.get("content", "").strip()
            target_client = next((c for c in clients if c["name"].lower() == target_name.lower() and c["status"] != "offline"), None)
            
            if target_client:
                send_packet(target_client["socket"], {
                    "type": "dm",
                    "sender": client["name"],
                    "content": content
                })
                send_packet(client_socket, {
                    "type": "dm_echo",
                    "target": target_name,
                    "content": content
                })
            else:
                send_packet(client_socket, {
                    "type": "system",
                    "content": f"SYSTEM: User '{target_name}' is offline.\n"
                })

        elif packet_type == "name_change":
            new_name = packet.get("name", "").strip()
            # Reject empty or whitespace-only names during name change requests
            if not new_name:
                send_packet(client_socket, {
                    "type": "name_rejected",
                    "reason": "empty"
                })
            elif contains_forbidden_words(new_name):
                send_packet(client_socket, {
                    "type": "name_rejected",
                    "reason": "blocked"
                })
            else:
                is_available, reason = name_is_available(new_name, exclude_client=client)
                if not is_available:
                    send_packet(client_socket, {
                        "type": "name_taken",
                        "name": new_name,
                        "reason": reason,
                        "allowed": ALLOWED_NAME_OPTIONS
                    })
                else:
                    old_name = client["name"]
                    if old_name != new_name:
                        if old_name not in client["name_history"]:
                            client["name_history"].append(old_name)
                        client["name"] = new_name
                        log_server_event(f"* {old_name} changed name to {new_name}")
                        broadcast_global({
                            "type": "system",
                            "content": f"[NICKNAME] {old_name} changed their nickname to {new_name}\n"
                        })
                        send_packet(client_socket, {"type": "name_changed", "name": new_name})
                        update_user_lists()
                        try:
                            if window.winfo_exists():
                                window.after(0, update_client_list_gui)
                        except Exception:
                            pass

        elif packet_type == "report":
            target_user = packet.get("target", "").strip()
            reason = packet.get("reason", "").strip()
            
            # --- Report Increment & Auto-Prompt Handler ---
            target_client = next((c for c in clients if c["name"].lower() == target_user.lower() and c["status"] != "offline"), None)
            if target_client:
                target_client["report_flags"] += 1
                report_entry = f"Reporter: {client['name']} | Accused: {target_client['name']} (Flags: {target_client['report_flags']}/6) | Violation: {reason}"
                user_reports.append(report_entry)
                log_server_event(f"[REPORT] {report_entry}")
                
                try:
                    if window.winfo_exists():
                        window.after(0, update_reports_gui)
                        
                        # If reports reach 6, prompt admin on the main GUI thread to prevent threading issues
                        if target_client["report_flags"] >= 6:
                            window.after(0, prompt_admin_to_boot, target_client)
                except Exception:
                    pass
            
            send_packet(client_socket, {
                "type": "system",
                "content": "✅ Incident reported and logged.\n"
            })

        elif packet_type == "file_share":
            filename = packet.get("filename")
            filedata = packet.get("filedata")
            sender = client["name"]
            broadcast_global({
                "type": "file_share_broadcast",
                "sender": sender,
                "filename": filename,
                "filedata": filedata
            })
            log_server_event(f"[FILES] {sender} uploaded file '{filename}'")

    remove_client(client)


def start_network_server():
    """Initializes the TCP listener socket, binds it to standard ports."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("0.0.0.0", CHAT_PORT))
        server.listen()
        log_server_event(f"Server listening on port {CHAT_PORT}")
    except Exception as e:
        log_server_event(f"Binding failed: {e}")
        return

    load_forbidden_words()
    load_allowed_names()
    loaded_hashes = load_allowed_client_hashes()
    log_server_event(f"Loaded {len(loaded_hashes)} approved client hash(es).")
    threading.Thread(target=broadcast_presence, daemon=True).start()

    while True:
        try:
            client_socket, address = server.accept()
            threading.Thread(target=handle_client, args=(client_socket, address), daemon=True).start()
        except Exception:
            break


# ============================================================
# ADMINISTRATIVE CONTROLS
# ============================================================

def prompt_admin_to_boot(target_client):
    """Prompts the admin inside a main thread popup dialog to verify report boots."""
    try:
        if target_client["status"] == "offline" or not target_client["socket"]:
            return
        
        ans = messagebox.askyesno("Confirm Incident Action", 
                                  f"User @{target_client['name']} has reached 6 report flags.\nShould they be booted from the server?")
        if ans:
            target_client["kicked"] = "policy"
            send_packet(target_client["socket"], {"type": "kicked_policy"})
            remove_client(target_client)
            log_server_event(f"[MOD] Booted @{target_client['name']} following report verification.")
    except Exception:
        pass


def open_web_redirect_panel():
    """Forces a client's computer to open a specific website inside their default web browser."""
    selected = client_listbox.curselection()
    if not selected:
        messagebox.showwarning("Admin Action", "Select an active client first.")
        return
    
    target_idx = selected[0]
    target_client = displayed_clients[target_idx]
    if target_client["status"] == "offline":
        messagebox.showwarning("Admin Action", "Selected client is currently offline.")
        return

    url = simpledialog.askstring("Open Web Link", f"Enter web link to open on {target_client['name']}'s browser:", initialvalue="https://")
    if url:
        url = url.strip()
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
            url = f"https://{url.lstrip('/') }"
        send_packet(target_client["socket"], {"type": "prank_url", "url": url})
        log_server_event(f"[ADMIN] Opened web link ({url}) on client: {target_client['name']}")


def play_sound_on_selected_user():
    """Sends a sound alert packet to the selected client computer."""
    selected = client_listbox.curselection()
    if not selected:
        messagebox.showwarning("Admin Action", "Select an active client first.")
        return

    target_client = displayed_clients[selected[0]]
    if target_client["status"] == "offline":
        messagebox.showwarning("Admin Action", "Selected client is currently offline.")
        return

    sound_style = simpledialog.askstring("Play Sound", "Enter sound type (beep, error, triple, alarm):", initialvalue="beep")
    if sound_style:
        send_packet(target_client["socket"], {"type": "prank_sound", "style": sound_style.strip().lower()})
        log_server_event(f"[ADMIN] Played sound ({sound_style}) on client: {target_client['name']}")


def mute_selected_user():
    """Mutes a selected user, preventing them from posting messages."""
    selected = client_listbox.curselection()
    if not selected:
        messagebox.showwarning("Admin Tools", "Select an active user first.")
        return
    target = displayed_clients[selected[0]]
    if target["status"] == "offline":
        return

    duration = simpledialog.askinteger("Mute User", "Enter mute duration (seconds):", minvalue=1, maxvalue=86400)
    if duration:
        target["mute_until"] = time.time() + duration
        log_server_event(f"[ADMIN] Muted {target['name']} for {duration}s.")
        broadcast_global({
            "type": "system",
            "content": f"[SYSTEM] {target['name']} has been muted for {duration} seconds.\n"
        })


def open_prank_selection_panel():
    """Opens a searchable window containing exactly 100 different themed overlays."""
    selected = client_listbox.curselection()
    if not selected:
        messagebox.showwarning("Admin Action", "Select an active client first.")
        return
    
    target_idx = selected[0]
    target_client = displayed_clients[target_idx]
    if target_client["status"] == "offline":
        messagebox.showwarning("Admin Action", "Selected client is currently offline.")
        return

    panel = tk.Toplevel(window)
    panel.title(f"Select Overlay Theme: {target_client['name']}")
    panel.geometry("420x540")
    panel.configure(bg=BG_MAIN)
    panel.resizable(False, False)

    tk.Label(panel, text="Search & Filter Overlays (100 Themes 2019-2026):", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, padx=15, pady=(15, 2))
    
    search_var = tk.StringVar()
    search_entry = tk.Entry(panel, textvariable=search_var, bg=BG_BOX, fg=FG_TEXT, insertbackground="black", bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, font=("Segoe UI", 10))
    search_entry.pack(fill=tk.X, padx=15, pady=5)
    search_entry.focus()

    # Split Selector Area
    split_frame = tk.Frame(panel, bg=BG_MAIN)
    split_frame.pack(fill=tk.X, padx=15, pady=5)
    tk.Label(split_frame, text="Split Grid Multiplier:", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
    
    split_spin = tk.Spinbox(split_frame, from_=1, to=100, width=5, bg=BG_BOX, fg=FG_TEXT, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, font=("Segoe UI", 10))
    split_spin.pack(side=tk.LEFT, padx=10)

    list_frame = tk.Frame(panel, bg=BG_MAIN)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    
    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    template_listbox = tk.Listbox(list_frame, bg=BG_BOX, fg=FG_TEXT, yscrollcommand=scrollbar.set, selectbackground=ACCENT_BLUE, selectforeground="white", bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, font=("Segoe UI", 9))
    template_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    scrollbar.config(command=template_listbox.yview)

    current_visible_templates = []

    def refresh_filtered_list(*args):
        """Filters 100 templates down dynamically in real-time as you type."""
        query = search_var.get().strip().lower()
        template_listbox.delete(0, tk.END)
        current_visible_templates.clear()
        
        for item in PRANK_DATABASE:
            if not query or query in item["name"].lower() or query in item["desc"].lower():
                template_listbox.insert(tk.END, f"  {item['name']} - {item['desc']}")
                current_visible_templates.append(item)

    search_var.trace_add("write", refresh_filtered_list)
    refresh_filtered_list()

    def send_selected_overlay():
        selected_sel = template_listbox.curselection()
        if not selected_sel:
            messagebox.showwarning("Admin Action", "Please select a theme from the filtered list.")
            return
        
        try:
            multiplier = int(split_spin.get())
            if multiplier < 1 or multiplier > 100:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Value Error", "Split count must be an integer between 1 and 100.")
            return

        chosen_item = current_visible_templates[selected_sel[0]]
        send_packet(target_client["socket"], {
            "type": "prank_popup",
            "style": chosen_item["id"],
            "name": chosen_item["name"],
            "splits": multiplier
        })
        log_server_event(f"[ADMIN] Sent Overlay ({chosen_item['name']}) with split factor {multiplier} to {target_client['name']}")
        panel.destroy()

    tk.Button(panel, text="Launch Fullscreen on Client", bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 10, "bold"), bd=0, command=send_selected_overlay).pack(fill=tk.X, padx=15, pady=15)


# ============================================================
# SERVER STANDARD GUI & CONTEXT MENU
# ============================================================

def show_user_context_menu(event):
    """Spawns an administrative context pop-up menu at the click location."""
    try:
        index = client_listbox.nearest(event.y)
        bbox = client_listbox.bbox(index)
        # Verify click falls strictly inside active item bounds
        if bbox and (bbox[1] <= event.y <= bbox[1] + bbox[3]):
            client_listbox.select_clear(0, tk.END)
            client_listbox.select_set(index)
            
            # Create popup context menu
            menu = tk.Menu(window, tearoff=0, bg=BG_BOX, fg=FG_TEXT, activebackground=ACCENT_BLUE, activeforeground="white")
            menu.add_command(label="Kick User", command=kick_selected_user)
            menu.add_command(label="Mute User", command=mute_selected_user)
            menu.add_command(label="Play Sound", command=play_sound_on_selected_user)
            menu.add_command(label="Send Fullscreen Overlay", command=open_prank_selection_panel)
            menu.add_command(label="Web Link Redirect", command=open_web_redirect_panel)
            menu.post(event.x_root, event.y_root)
    except Exception:
        pass


def log_server_event(text):
    """Safely schedules log update on the Tkinter main event thread."""
    try:
        window.after(0, _append_log_gui, text)
    except Exception:
        print(f"[{time.strftime('%H:%M:%S')}] {text}")


def _append_log_gui(text):
    """Appends server logs safely inside the log textbox."""
    try:
        server_log.config(state=tk.NORMAL)
        server_log.insert(tk.END, f"{time.strftime('[%H:%M:%S]')} " + text + "\n")
        server_log.config(state=tk.DISABLED)
        server_log.see(tk.END)
    except Exception:
        pass


def update_client_list_gui():
    """Refreshes the rendered list of active users."""
    try:
        if not window.winfo_exists():
            return
        client_listbox.delete(0, tk.END)
        global displayed_clients
        displayed_clients = [c for c in clients if c["status"] != "offline"]
        for client in displayed_clients:
            client_listbox.insert(tk.END, f" {client['name']}")
    except Exception:
        pass


def update_reports_gui():
    """Refreshes the security warnings listbox."""
    try:
        if not window.winfo_exists():
            return
        reports_listbox.delete(0, tk.END)
        for report in user_reports:
            reports_listbox.insert(tk.END, f" [WARNING] {report}")
    except Exception:
        pass


def periodic_cleanup_task():
    """Runs every 5 seconds to permanently prune inactive clients."""
    try:
        if window.winfo_exists():
            current_time = time.time()
            modified = False
            for client in list(clients):
                if client["status"] == "offline":
                    if client["disconnect_time"] and (current_time - client["disconnect_time"] > 300):
                        clients.remove(client)
                        modified = True
            if modified:
                update_client_list_gui()
            window.after(5000, periodic_cleanup_task)
    except Exception:
        pass


class Tooltip:
    """Creates a basic hovering pop-up window containing client details."""
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.active_index = -1

    def show_tip(self, text, x, y):
        if self.tip_window or not text:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x + 15}+{y + 10}")
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "9", "normal"), padx=5, pady=3)
        label.pack()

    def hide_tip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


def on_listbox_motion(event):
    """Detects where mouse is hovering on the client listbox."""
    try:
        index = client_listbox.nearest(event.y)
        bbox = client_listbox.bbox(index)
        if bbox and (bbox[1] <= event.y <= bbox[1] + bbox[3]):
            if index < len(displayed_clients):
                if tooltip.active_index != index:
                    tooltip.hide_tip()
                    client = displayed_clients[index]
                    info_text = f"Name: {client['name']}\nIP: {client['addr'][0]}\nConnection Status: {client['status'].upper()}"
                    tooltip.show_tip(info_text, event.x_root, event.y_root)
                    tooltip.active_index = index
                return
        tooltip.hide_tip()
        tooltip.active_index = -1
    except Exception:
        pass


def kick_selected_user():
    """Forces selected listbox client to disconnect."""
    selected_indices = client_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Admin Action", "Select an active client to kick.")
        return
    index = selected_indices[0]
    if index < len(displayed_clients):
        target = displayed_clients[index]
        if target["status"] == "offline":
            return
        target["kicked"] = "admin"
        send_packet(target["socket"], {"type": "kicked_admin"})
        remove_client(target)


def send_admin_broadcast():
    """Dispatches an announcement to all clients."""
    text = admin_input.get().strip()
    if text:
        broadcast_global({
            "type": "message",
            "sender": "SYSTEM-BOT",
            "content": f"**[ANNOUNCEMENT]** {text}"
        })
        log_server_event(f"[ADMIN BROADCAST] {text}")
        admin_input.delete(0, tk.END)


def shutdown_network_system():
    """Prompts server teardown, safely ejecting everyone."""
    if messagebox.askyesno("Global Shutdown", "Shutdown server and disconnect all clients?"):
        broadcast_global({"type": "server_shutdown"})
        time.sleep(1)
        on_server_close()


def on_server_close():
    """Closes all clients sockets and closes window safely."""
    for client in list(clients):
        client["kicked"] = "shutdown"
        if client["socket"]:
            try:
                client["socket"].close()
            except Exception:
                pass
    window.destroy()


def auto_scale_server_font(event):
    """Dynamically scales the activity log text font size when the window is resized."""
    if event.widget == window:
        # Scale factor based on baseline dimensions 900x520
        scale = min(window.winfo_width() / 900, window.winfo_height() / 520)
        new_size = max(6, min(14, int(9 * scale)))
        server_log.configure(font=("Courier New", new_size))


# ============================================================
# MAIN WINDOW SYSTEM & INTERFACE SETUP
# ============================================================

window = tk.Tk()
window.title("Chat Control Panel")
window.geometry("900x520")
window.configure(bg=BG_MAIN) # Pure white background

style = ttk.Style()
style.theme_use("clam")

# Multi-column layout container
panels_frame = tk.Frame(window, bg=BG_MAIN)
panels_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# 1. Left Column: Event Logs (Configured as light Grey Box)
log_frame = tk.LabelFrame(panels_frame, text="Server Activity Log", bg=BG_BOX, fg=ACCENT_BLUE, bd=1, relief=tk.SOLID, font=("Segoe UI", 10, "bold"))
log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

server_log = tk.Text(log_frame, state=tk.DISABLED, wrap=tk.WORD, width=38, bg=BG_BOX, fg=FG_TEXT, insertbackground="black", font=("Courier New", 9), bd=0)
server_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# 2. Center Column: Connected Users List (Double/Right Click to activate Menu)
control_frame = tk.Frame(panels_frame, bg=BG_MAIN)
control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

users_frame = tk.LabelFrame(control_frame, text="Connected Users", bg=BG_BOX, fg=ACCENT_BLUE, bd=1, relief=tk.SOLID, font=("Segoe UI", 10, "bold"))
users_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

client_listbox = tk.Listbox(users_frame, width=30, bg=BG_BOX, fg=FG_TEXT, selectbackground=ACCENT_BLUE, selectforeground="white", bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, font=("Segoe UI", 10))
client_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Bind left double click and right click options onto target lists
client_listbox.bind("<Double-Button-1>", show_user_context_menu)
client_listbox.bind("<Button-3>", show_user_context_menu) # Right-click on Windows
client_listbox.bind("<Button-2>", show_user_context_menu) # Right-click on macOS

tooltip = Tooltip(client_listbox)
client_listbox.bind("<Motion>", on_listbox_motion)
client_listbox.bind("<Leave>", lambda e: tooltip.hide_tip())

# 3. Right Column: Incident Audit Logger
right_frame = tk.Frame(panels_frame, bg=BG_MAIN)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

reports_frame = tk.LabelFrame(right_frame, text="Security Audit Log", bg=BG_BOX, fg=ACCENT_BLUE, bd=1, relief=tk.SOLID, font=("Segoe UI", 10, "bold"))
reports_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

reports_listbox = tk.Listbox(reports_frame, bg=BG_BOX, fg=ACCENT_RED, selectbackground=ACCENT_RED, selectforeground="white", bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, font=("Segoe UI", 9), height=8)
reports_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

admin_frame = tk.LabelFrame(right_frame, text="Server Broadcast Terminal", bg=BG_BOX, fg=ACCENT_BLUE, bd=1, relief=tk.SOLID, font=("Segoe UI", 10, "bold"))
admin_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

admin_input = tk.Entry(admin_frame, bg=BG_BOX, fg=FG_TEXT, insertbackground="black", bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, font=("Segoe UI", 10))
admin_input.pack(fill=tk.X, padx=10, pady=6)

send_admin_button = tk.Button(admin_frame, text="Broadcast Announcement", bg="#2E7D32", fg="white", font=("Segoe UI", 9, "bold"), bd=0, activebackground="#1B5E20", activeforeground="white", command=send_admin_broadcast)
send_admin_button.pack(fill=tk.X, padx=10, pady=4)

shutdown_button = tk.Button(admin_frame, text="Shutdown Server", command=shutdown_network_system, bg=ACCENT_RED, fg="white", font=("Segoe UI", 9, "bold"), bd=0, activebackground="#B71C1C")
shutdown_button.pack(fill=tk.X, padx=10, pady=6)

# Launch background execution threads
server_thread = threading.Thread(target=start_network_server, daemon=True)
server_thread.start()

# Bind dynamic size tracking to font auto-scaler
window.bind("<Configure>", auto_scale_server_font)

window.after(1000, periodic_cleanup_task)
window.protocol("WM_DELETE_WINDOW", on_server_close)
window.mainloop()
