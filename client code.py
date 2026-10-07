# ==============================================================================
# CHAT CLIENT CODE - CLEAN WHITE THEME & INLINE LAYOUT (NO EMOJIS / STATUSES)
# ==============================================================================

# Import built-in Python libraries (no extra installation needed!)
import socket      # Handles network connections (TCP/UDP)
import os          # Interacts with local files and path operations
import sys         # Controls system level parameters
import struct      # Translates Python variables to structured binary formats
import threading   # Runs tasks concurrently on background execution threads
import hashlib     # Generates hash values used here for script verification
import webbrowser  # Directs links to be opened inside default desktop web browser
import time        # Tracks time formats and clock ticks
import json        # Serializes and deserializes structured network dictionaries
import base64      # Safely converts binary raw bytes into string text formats
import re          # Regular expressions library used for parsing markdown strings
import math        # Mathematical helpers for overlay split grid calculations
import getpass     # Reads the current Windows login username to send to the server
import subprocess  # Runs the Windows 'shutdown' command when the admin requests it
import ctypes      # Reads an image off the Windows clipboard for paste-to-chat
import tkinter as tk # Main package used for constructing the GUI layout
from tkinter import messagebox, simpledialog, filedialog, ttk # Popup boxes

# ------------------------------------------------------------------------------
# GLOBAL CLIENT SETTINGS & LOOKS
# ------------------------------------------------------------------------------
DISCOVERY_PORT = 50001 # Listening port for UDP server discovery broadcast
name = ""              # Stores current chosen username profile
room_members = []      # Tracks active directory list of users online in the chat
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_NAME_OPTIONS = [] # Usernames downloaded from the server's built-in list
NAMES_IN_USE = []         # Names from that list that are already logged in
WINDOWS_USER = getpass.getuser() # Real Windows login name, reported to the server
shared_files = {}         # Maps a link id -> (filename, base64 data) for downloads
_file_link_counter = 0    # Increments to give each shared-file link a unique tag

# Stark styling design constants to create light box components
BG_MAIN = "#FFFFFF"      # Pure white background
BG_BOX = "#F5F7F8"       # Soft light-grey boxes/panels for widgets
FG_TEXT = "#1C1E21"      # Dark charcoal text for comfortable reading
ACCENT_BLUE = "#0066CC"  # Clean professional blue
ACCENT_RED = "#D32F2F"   # Warning/alert red
BORDER_COLOR = "#D0D0D0" # Crisp borders separating functional areas


def calculate_file_hash():
    """
    Reads this script file and generates a SHA-256 integrity fingerprint.
    Normalizes newlines so changing code from Windows to Linux editors doesn't break.
    """
    try:
        path = __file__ # Points to the path location of this running script
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        # Clean line breaks to ensure uniform hash calculations
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.rstrip() for line in normalized.split("\n")]
        normalized_content = "\n".join(lines).strip()
        return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
    except Exception:
        return "DEFAULT_IDLE_CLIENT_TOKEN_v3.0"


def connect_to_server():
    """Finds the server and opens the TCP socket."""
    server_ip, server_port = find_server()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))
    return sock

# ------------------------------------------------------------------------------
# PACKET TRANSMISSION UTILITIES (TCP STREAM WRAPPERS)
# ------------------------------------------------------------------------------
def send_packet(sock, data_dict):
    """Packages and sends a Python dictionary to the server."""
    try:
        data = json.dumps(data_dict).encode("utf-8")
        header = struct.pack("!I", len(data)) # Encodes text length as 4 binary bytes
        sock.sendall(header + data)
    except Exception as e:
        if "window" in globals() and "chat_log" in globals():
            display_message(f"Transmission failed: {e}\n", "system_tag")
        else:
            print(f"Transmission failed: {e}")


def recv_packet(sock):
    """Listens for and reconstructs a framed message package from the server."""
    try:
        header = recv_all(sock, 4) # Extract length descriptor first
        if not header:
            return None
        length = struct.unpack("!I", header)[0] # Extract structural count
        data = recv_all(sock, length)
        if not data:
            return None
        return json.loads(data.decode("utf-8")) # Return structured dictionary
    except Exception:
        return None


def recv_all(sock, n):
    """Guarantees reading precisely 'n' bytes from TCP stream socket."""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def find_server():
    """
    Listens for UDP broad packets to find the server automatically.
    This bypasses needing to manually input IP addresses.
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(("", DISCOVERY_PORT))
    data, address = udp_socket.recvfrom(1024)
    message = data.decode()
    if message.startswith("CHAT_SERVER"):
        port = int(message.split()[1])
        server_ip = address[0] # Extracted source server IP
        udp_socket.close()
        return server_ip, port

# ------------------------------------------------------------------------------
# CLIENT BACKSTAGE EVENT ROUTER
# ------------------------------------------------------------------------------
def receive_messages():
    """
    Runs in a background thread to continually listen for incoming packets
    from the server socket, routing them to appropriate interface operations.
    """
    global room_members
    while True:
        packet = recv_packet(server)
        if packet is None:
            display_message("Disconnected from server.\n", "system_tag")
            break
        
        packet_type = packet.get("type")

        # Kick/Shut down trigger cases
        if packet_type == "kicked_policy":
            window.after(0, terminate_app, "Violation", "You were disconnected for violating content rules.")
            break
        elif packet_type == "kicked_admin":
            window.after(0, terminate_app, "Kicked", "You have been kicked from the server.")
            break
        elif packet_type == "server_shutdown":
            window.after(0, terminate_app, "Server Offline", "The server has shut down.")
            break
        elif packet_type == "name_changed":
            new_name = packet.get("name")
            window.after(0, update_window_title, new_name)
            continue
        elif packet_type == "name_taken":
            chosen_name = packet.get("name", "")
            reason = packet.get("reason", "taken")
            if reason == "not_allowed" and ALLOWED_NAME_OPTIONS:
                message = f"@{chosen_name} is not in the approved name list."
            elif reason == "empty":
                message = "Username cannot be empty."
            else:
                message = f"@{chosen_name} is already in use."
            window.after(0, messagebox.showwarning, "Nickname Unavailable", message)
            continue
        elif packet_type == "name_rejected":
            reason = packet.get("reason", "blocked")
            if reason == "empty":
                message = "Username cannot be empty."
            elif reason == "blocked":
                message = "That username is not allowed."
            else:
                message = "Username rejected."
            window.after(0, messagebox.showwarning, "Nickname Rejected", message)
            continue
        elif packet_type == "reject_integrity":
            window.after(0, terminate_app, "Hash Error", "This client code is not approved by the server.")
            break
            
        # Prank Redirect injection handlers
        elif packet_type == "prank_sound":
            sound_style = packet.get("style", "beep")
            window.after(0, execute_sound_alert, sound_style)
            continue
        elif packet_type == "prank_url":
            target_url = packet.get("url")
            window.after(0, execute_open_url, target_url)
            continue
        elif packet_type == "shutdown_pc":
            reason = packet.get("reason", "An administrator has shut down this computer.")
            # Tell the server we received the command, so the admin can see it landed.
            try:
                send_packet(server, {"type": "shutdown_ack"})
            except Exception:
                pass
            window.after(0, execute_pc_shutdown, reason)
            continue
        elif packet_type == "prank_popup":
            popup_style = packet.get("style", "overlay_1")
            popup_name = packet.get("name", "Alert Overlay")
            splits = packet.get("splits", 1) # Extract multi-grid count (defaults to 1)
            window.after(0, execute_popup_variant, popup_style, popup_name, splits)
            continue
        elif packet_type == "image_overlay":
            image_data = packet.get("image", "")
            window.after(0, execute_image_overlay, image_data)
            continue
            
        # Directory layout refreshes
        elif packet_type == "user_list_update":
            room_members = packet.get("members", [])
            window.after(0, update_room_members_gui)
            continue
            
        # Message processing
        elif packet_type == "message":
            sender = packet.get("sender", "System")
            content = packet.get("content", "")
            
            # Print timestamp first
            timestamp = time.strftime("[%H:%M:%S] ")
            display_message_header(timestamp, "timestamp_tag")
            
            # Determine if it's our own message or an outside peer's message
            if sender.lower() == name.lower():
                # For our own message, name goes on the left in high-contrast blue, labeled as (You)
                display_message_header(f"{sender} (You): ", "own_member_tag")
            else:
                # Outside peer's message on the left
                display_message_header(f"{sender}: ", "member_tag")
            
            # Parse markdown and print body segment on the same line
            display_parsed_markdown_message(f"{content}\n")
            
        elif packet_type == "dm":
            sender = packet.get("sender", "Anonymous")
            content = packet.get("content", "")
            display_message(f"[Private] [From {sender}]: {content}\n", "dm_received_tag")
        elif packet_type == "dm_echo":
            target = packet.get("target")
            content = packet.get("content")
            display_message(f"[Private] [To {target}]: {content}\n", "dm_sent_tag")
        elif packet_type == "system":
            content = packet.get("content", "")
            display_message(content, "system_tag")
        elif packet_type == "file_share_broadcast":
            sender = packet.get("sender")
            filename = packet.get("filename")
            filedata = packet.get("filedata")
            window.after(0, insert_file_link, sender, filename, filedata)


# ------------------------------------------------------------------------------
# INJECTED ACTIONS (DYNAMIC FULLSCREEN RENDERING ENGINE)
# ------------------------------------------------------------------------------
def execute_sound_alert(sound_type):
    """Triggers sound alarms using Windows winsound library."""
    try:
        import winsound
        if sound_type == "error":
            winsound.Beep(300, 600)
        elif sound_type == "triple":
            for _ in range(3):
                winsound.Beep(1200, 150)
                time.sleep(0.1)
        elif sound_type == "alarm":
            for _ in range(4):
                winsound.Beep(800, 200)
                winsound.Beep(1000, 200)
        else:
            winsound.MessageBeep()
    except Exception:
        # Fallback cross-platform shell bell alert
        sys.stdout.write("\a")
        sys.stdout.flush()


def execute_open_url(url):
    """Launches website link within default device browser."""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = f"https://{url.lstrip('/')}"
    webbrowser.open_new_tab(url)


def execute_pc_shutdown(reason):
    """Shows a clear notice, then triggers a real Windows shutdown of this PC.

    This is intentionally visible (not hidden): a full-screen message tells the
    user what is happening before the short shutdown timer runs.
    """
    # Show a clear, top-most notice so the shutdown is never silent
    try:
        notice = tk.Toplevel(window)
        notice.attributes("-fullscreen", True)
        notice.attributes("-topmost", True)
        notice.configure(bg="#000000")
        tk.Label(
            notice,
            text=f"{reason}\n\nThis computer will shut down in a few seconds.",
            bg="#000000", fg="#FFFFFF", font=("Segoe UI", 20, "bold"),
            justify=tk.CENTER, wraplength=900
        ).pack(expand=True)
        notice.update()
    except Exception:
        pass

    # Trigger the real OS shutdown. A short timer keeps the notice visible.
    # (During testing, 'shutdown /a' in a terminal aborts before it fires.)
    if not sys.platform.startswith("win"):
        # Non-Windows: do not run a destructive fallback; just log it.
        print(f"[SHUTDOWN REQUEST] {reason} (no action taken on this platform)")
        return
    try:
        result = subprocess.run(
            ["shutdown", "/s", "/t", "5", "/c", reason],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            capture_output=True, text=True
        )
        if result.returncode != 0:
            # Most common cause on managed/school PCs: the account lacks the
            # shutdown privilege (error 5, Access denied). Surface it rather
            # than failing silently, so the reason is visible during testing.
            detail = (result.stderr or result.stdout or "").strip()
            messagebox.showerror(
                "Shutdown Failed",
                f"The shutdown command returned error {result.returncode}.\n{detail}"
            )
    except Exception as e:
        messagebox.showerror("Shutdown Failed", f"Could not run the shutdown command:\n{e}")


def _make_fullscreen_overlay(auto_dismiss_ms=8000):
    """Creates a fullscreen, top-most overlay window that can't be clicked past.

    It dismisses itself after a timeout and can be closed with the Escape key.
    Returns (popup, canvas).
    """
    popup = tk.Toplevel(window)
    popup.attributes("-fullscreen", True)
    popup.attributes("-topmost", True)
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    popup.grab_set()

    canvas = tk.Canvas(popup, highlightthickness=0, bg="#000000")
    canvas.pack(fill=tk.BOTH, expand=True)

    def unlock_overlay(event=None):
        try:
            popup.grab_release()
            popup.destroy()
        except Exception:
            pass

    popup.after(auto_dismiss_ms, unlock_overlay)
    popup.bind("<Escape>", unlock_overlay)
    return popup, canvas


def execute_popup_variant(popup_style, popup_name, splits=1):
    """Shows a fullscreen text overlay, optionally tiled across a grid."""
    popup, canvas = _make_fullscreen_overlay()
    sw = popup.winfo_screenwidth()
    sh = popup.winfo_screenheight()

    # The message is the template name without the trailing " - Style N" label.
    message = popup_name.split(" - ")[0] if popup_name else "ALERT"

    # Lay the message out across a grid based on the requested split count.
    splits = max(1, int(splits))
    cols = int(math.ceil(math.sqrt(splits)))
    rows = int(math.ceil(splits / cols))
    tile_width = sw // cols
    tile_height = sh // rows
    font_size = max(10, int(min(tile_width, tile_height) * 0.12))

    for i in range(splits):
        r = i // cols
        c = i % cols
        cx = c * tile_width + tile_width // 2
        cy = r * tile_height + tile_height // 2
        canvas.create_text(
            cx, cy, text=message, fill="#FFFFFF",
            font=("Segoe UI", font_size, "bold"),
            width=int(tile_width * 0.9), justify=tk.CENTER
        )


def execute_image_overlay(b64_image):
    """Shows an admin-supplied image fullscreen on this client's screen."""
    popup, canvas = _make_fullscreen_overlay()
    sw = popup.winfo_screenwidth()
    sh = popup.winfo_screenheight()

    try:
        popup.overlay_image = tk.PhotoImage(data=b64_image)
    except Exception:
        # tkinter only reads PNG/GIF; anything else can't be shown.
        canvas.create_text(sw // 2, sh // 2, text="(Unsupported image format)", fill="#FFFFFF", font=("Segoe UI", 20, "bold"))
        return

    # Scale with integer zoom/subsample to roughly fill the screen (no Pillow).
    img = popup.overlay_image
    iw, ih = img.width(), img.height()
    if iw > 0 and ih > 0:
        if iw < sw and ih < sh:
            factor = max(1, min(sw // iw, sh // ih))
            if factor > 1:
                img = img.zoom(factor)
        elif iw > sw or ih > sh:
            factor = max(1, max(-(-iw // sw), -(-ih // sh)))
            img = img.subsample(factor)
        popup.overlay_image = img

    canvas.create_image(sw // 2, sh // 2, image=popup.overlay_image)


# ------------------------------------------------------------------------------
# USER ACTION DIALOGS & PANELS
# ------------------------------------------------------------------------------
def open_prefilled_report_dialog(target_name):
    """Opens report ticket window with accused username pre-filled."""
    rep_win = tk.Toplevel(window)
    rep_win.title(f"Report User: @{target_name}")
    rep_win.geometry("320x200")
    rep_win.configure(bg=BG_MAIN)
    rep_win.resizable(False, False)
    
    tk.Label(rep_win, text=f"REPORTING USER: @{target_name}", font=("Segoe UI", 9, "bold"), bg=BG_MAIN, fg=ACCENT_RED).pack(anchor=tk.W, padx=15, pady=(15, 2))
    
    tk.Label(rep_win, text="REASON FOR REPORT:", font=("Segoe UI", 9, "bold"), bg=BG_MAIN, fg=FG_TEXT).pack(anchor=tk.W, padx=15, pady=(10, 2))
    reason_entry = tk.Entry(rep_win, bg=BG_BOX, fg=FG_TEXT, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, insertbackground="black")
    reason_entry.pack(fill=tk.X, padx=15, pady=5)
    reason_entry.focus()
    
    def submit_report():
        reason = reason_entry.get().strip()
        if reason:
            send_packet(server, {"type": "report", "target": target_name, "reason": reason})
            rep_win.destroy()
        else:
            messagebox.showwarning("Incomplete", "Reason field is required.")

    tk.Button(rep_win, text="Submit Moderation Ticket", command=submit_report, bg=ACCENT_RED, fg="white", font=("Segoe UI", 9, "bold"), bd=0).pack(fill=tk.X, padx=15, pady=15)


def open_private_message_dialog(target_name):
    """Launches instant prompt dialogue to send custom Direct Messages."""
    if target_name == name:
        messagebox.showwarning("Direct Message", "You cannot send direct messages to yourself.")
        return
    
    text = simpledialog.askstring("Direct Message", f"Send Private Message to @{target_name}:", parent=window)
    if text and text.strip():
        send_packet(server, {
            "type": "dm",
            "target": target_name,
            "content": text.strip()
        })


def get_clipboard_image_bmp():
    """Returns a .bmp byte string of any image on the Windows clipboard, else None.

    Uses only ctypes (no Pillow). The clipboard stores images as a 'DIB', which is
    a BMP file minus its 14-byte file header, so we read the DIB and prepend that
    header. Returns None on non-Windows systems or when there is no image.
    """
    if not sys.platform.startswith("win"):
        return None
    CF_DIB = 8
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.IsClipboardFormatAvailable.argtypes = [ctypes.c_uint]
    user32.GetClipboardData.argtypes = [ctypes.c_uint]
    user32.GetClipboardData.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalSize.argtypes = [ctypes.c_void_p]
    kernel32.GlobalSize.restype = ctypes.c_size_t

    if not user32.OpenClipboard(None):
        return None
    try:
        if not user32.IsClipboardFormatAvailable(CF_DIB):
            return None
        handle = user32.GetClipboardData(CF_DIB)
        if not handle:
            return None
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return None
        try:
            size = kernel32.GlobalSize(handle)
            dib = ctypes.string_at(ptr, size)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()

    if len(dib) < 40:
        return None
    header_size = struct.unpack_from("<I", dib, 0)[0]
    bit_count = struct.unpack_from("<H", dib, 14)[0]
    colors_used = struct.unpack_from("<I", dib, 32)[0]
    # Work out where the pixel data starts (after the header + any colour palette).
    if bit_count < 16:
        palette = colors_used if colors_used else (1 << bit_count)
    else:
        palette = colors_used
    pixel_offset = 14 + header_size + palette * 4
    file_size = 14 + len(dib)
    bmp_header = b"BM" + struct.pack("<IHHI", file_size, 0, 0, pixel_offset)
    return bmp_header + dib


def paste_image_to_chat(event=None):
    """If the clipboard holds an image, share it to the chat as an attachment.

    Bound to Ctrl+V: when there's no image, returns None so normal text paste
    still happens; when there is one, sends it and returns 'break' to stop the
    image bytes being dumped into the text box.
    """
    try:
        bmp = get_clipboard_image_bmp()
    except Exception:
        bmp = None
    if not bmp:
        return None  # let the default text paste proceed

    if len(bmp) > 20 * 1024 * 1024:
        messagebox.showerror("Limit Exceeded", "Pasted image is too large (limit 20MB).")
        return "break"

    filename = f"pasted_image_{time.strftime('%H%M%S')}.bmp"
    b64_str = base64.b64encode(bmp).decode("utf-8")
    send_packet(server, {"type": "file_share", "filename": filename, "filedata": b64_str})
    return "break"


def send_file_dialog():
    """Opens local system explorer prompt allowing user to select and upload any file."""
    path = filedialog.askopenfilename()
    if path:
        filename = os.path.basename(path)
        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
                # Limit size to 20MB
                if len(raw_bytes) > 20 * 1024 * 1024:
                    messagebox.showerror("Limit Exceeded", "File size cannot exceed 20MB.")
                    return
                # Convert binary data to string safe representation
                b64_str = base64.b64encode(raw_bytes).decode("utf-8")
                send_packet(server, {
                    "type": "file_share",
                    "filename": filename,
                    "filedata": b64_str
                })
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")


def insert_file_link(sender, filename, b64_str):
    """Writes a clickable download link into the chat log for a shared file."""
    global _file_link_counter
    _file_link_counter += 1
    link_tag = f"filelink_{_file_link_counter}"
    shared_files[link_tag] = (filename, b64_str)

    # Style this link and make it behave like a hyperlink (blue, underlined, hand cursor)
    chat_log.tag_config(link_tag, foreground=ACCENT_BLUE, underline=True, font=("Segoe UI", 10, "bold"))
    chat_log.tag_bind(link_tag, "<Button-1>", lambda event, t=link_tag: _on_file_link_click(t))
    chat_log.tag_bind(link_tag, "<Enter>", lambda event: chat_log.config(cursor="hand2"))
    chat_log.tag_bind(link_tag, "<Leave>", lambda event: chat_log.config(cursor=""))

    chat_log.config(state=tk.NORMAL)
    y_scroll = chat_log.yview()
    at_bottom = y_scroll[1] >= 0.99
    timestamp = time.strftime("[%H:%M:%S] ")
    chat_log.insert(tk.END, timestamp, "timestamp_tag")
    chat_log.insert(tk.END, f"{sender} shared a file: ", "file_tag")
    chat_log.insert(tk.END, f"{filename} (click to download)\n", link_tag)
    chat_log.config(state=tk.DISABLED)
    if at_bottom:
        chat_log.see(tk.END)


def _on_file_link_click(link_tag):
    """Handles a click on a shared-file link and starts the download."""
    entry = shared_files.get(link_tag)
    if entry:
        filename, b64_str = entry
        prompt_save_file(filename, b64_str)


def prompt_save_file(filename, b64_str):
    """Asks user if they wish to download an attachment being shared on screen."""
    if messagebox.askyesno("File Shared", f"Do you want to download shared attachment: '{filename}'?"):
        save_path = filedialog.asksaveasfilename(initialfile=filename)
        if save_path:
            try:
                # Decrypt text string back into structural binary file output
                raw_data = base64.b64decode(b64_str.encode("utf-8"))
                with open(save_path, "wb") as f:
                    f.write(raw_data)
                messagebox.showinfo("Successful", "File saved.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")


def show_peer_context_menu(event):
    """Launches custom interactive context menus on member list selection."""
    try:
        index = peers_listbox.nearest(event.y)
        line = peers_listbox.get(index).strip()
        
        # Verify focus is not set on header lines
        if line == "CONNECTED USERS" or not line:
            return
            
        peers_listbox.select_clear(0, tk.END)
        peers_listbox.select_set(index)
        
        # Resolve targeted peer name
        target_name = None
        for m in room_members:
            if m["name"] in line:
                target_name = m["name"]
                break
                
        if not target_name:
            return
            
        # Draw context popup
        menu = tk.Menu(window, tearoff=0, bg=BG_BOX, fg=FG_TEXT, activebackground=ACCENT_BLUE, activeforeground="white")
        menu.add_command(label=f"Private Message @{target_name}", command=lambda: open_private_message_dialog(target_name))
        menu.add_command(label=f"Report @{target_name}", command=lambda: open_prefilled_report_dialog(target_name))
        menu.post(event.x_root, event.y_root)
    except Exception:
        pass


class PeerTooltip:
    """Shows hover details for a peer in the member list."""
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


def on_peer_list_motion(event):
    """Updates the peer hover tooltip when the mouse moves over a name."""
    try:
        index = peers_listbox.nearest(event.y)
        bbox = peers_listbox.bbox(index)
        if bbox and (bbox[1] <= event.y <= bbox[1] + bbox[3]) and index > 0:
            member_index = index - 1
            if member_index < len(room_members):
                if peer_tooltip.active_index != index:
                    peer_tooltip.hide_tip()
                    member = room_members[member_index]
                    previous_names = member.get("previous_names", [])
                    if previous_names:
                        previous_text = ", ".join(previous_names)
                    else:
                        previous_text = "None"
                    info_text = f"Name: {member['name']}\nPrevious names: {previous_text}"
                    peer_tooltip.show_tip(info_text, event.x_root, event.y_root)
                    peer_tooltip.active_index = index
                return
        peer_tooltip.hide_tip()
        peer_tooltip.active_index = -1
    except Exception:
        pass


def terminate_app(reason, detail):
    """Dismisses application with informational status popup."""
    messagebox.showinfo(reason, detail)
    on_closing()

# ------------------------------------------------------------------------------
# CHAT RENDERING ENGINE
# ------------------------------------------------------------------------------
def display_message(message, tag):
    """Safely queues string messages to write on text logger box."""
    if "window" in globals():
        window.after(0, _add_to_chat_log, message, tag)
    else:
        print(message, end="")


def display_message_header(chunk, tag):
    """Queues writing styling headers directly on text log."""
    if "window" in globals():
        window.after(0, _add_chunk_to_chat_log, chunk, tag)
    else:
        print(chunk, end="")


def _add_chunk_to_chat_log(chunk, tag):
    """Appends formatting text strings directly without adding newlines."""
    chat_log.config(state=tk.NORMAL)
    chat_log.insert(tk.END, chunk, tag)
    chat_log.config(state=tk.DISABLED)


def _add_to_chat_log(message, tag):
    """Inserts timed formatted chat items to view frame."""
    chat_log.config(state=tk.NORMAL)
    y_scroll = chat_log.yview()
    at_bottom = y_scroll[1] >= 0.99
    
    timestamp = time.strftime("[%H:%M:%S] ")
    chat_log.insert(tk.END, timestamp, "timestamp_tag")
    chat_log.insert(tk.END, message, tag)
    chat_log.config(state=tk.DISABLED)
    
    # Auto-scroll view if user was already at the bottom
    if at_bottom:
        chat_log.see(tk.END)
    else:
        new_msg_button.pack(fill=tk.X, side=tk.BOTTOM, before=bottom_frame)


def display_parsed_markdown_message(content):
    """Schedules basic text formatting parsing."""
    if "window" in globals():
        window.after(0, _parse_and_append_markdown, content)
    else:
        print(content, end="")


def _parse_and_append_markdown(content):
    """Scans and maps basic markdown tags (**bold**, *italics*, etc.)."""
    chat_log.config(state=tk.NORMAL)
    y_scroll = chat_log.yview()
    at_bottom = y_scroll[1] >= 0.99
    
    # Slice text by basic formatting keywords (Uses imported 're' library)
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*|__.*?__|~~.*?~~|`.*?`)', content)
    for token in tokens:
        if token.startswith("**") and token.endswith("**"):
            clean = token[2:-2]
            chat_log.insert(tk.END, clean, "bold_tag")
        elif token.startswith("*") and token.endswith("*"):
            clean = token[1:-1]
            chat_log.insert(tk.END, clean, "italic_tag")
        elif token.startswith("__") and token.endswith("__"):
            clean = token[2:-2]
            chat_log.insert(tk.END, clean, "underline_tag")
        elif token.startswith("~~") and token.endswith("~~"):
            clean = token[2:-2]
            chat_log.insert(tk.END, clean, "strike_tag")
        elif token.startswith("`") and token.endswith("`"):
            clean = token[1:-1]
            chat_log.insert(tk.END, clean, "code_tag")
        else:
            chat_log.insert(tk.END, token, "msg_tag")
            
    chat_log.config(state=tk.DISABLED)
    if at_bottom:
        chat_log.see(tk.END)


def scroll_to_bottom():
    """Forces chat logger scroll position to snap down."""
    chat_log.config(state=tk.NORMAL)
    chat_log.see(tk.END)
    chat_log.config(state=tk.DISABLED)
    new_msg_button.pack_forget()


def send_message(event=None):
    """Reads input box to send structural message to the server."""
    message = message_input.get()
    if message:
        send_packet(server, {"type": "message", "content": message})
        message_input.delete(0, tk.END)


def request_name_change():
    """Shows the server's name list so the user can pick a new nickname."""
    try:
        fetch_name_options()
    except Exception as e:
        messagebox.showwarning("Change Name", f"Could not load names from server: {e}")
        return

    if not ALLOWED_NAME_OPTIONS:
        messagebox.showinfo("Change Name", "The server has no usernames set up.")
        return

    picker_win = tk.Toplevel(window)
    picker_win.title("Change Name")
    picker_win.geometry("300x360")
    picker_win.configure(bg=BG_MAIN)
    picker_win.resizable(False, False)
    picker_win.transient(window)

    tk.Label(picker_win, text="Pick a new username:", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack(pady=(15, 5))

    list_frame = tk.Frame(picker_win, bg=BG_MAIN)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=20)
    scroll = tk.Scrollbar(list_frame)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    name_list = tk.Listbox(list_frame, bg=BG_BOX, fg=FG_TEXT, font=("Segoe UI", 10), justify=tk.CENTER, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, selectbackground=ACCENT_BLUE, selectforeground="white", activestyle="none", exportselection=False, yscrollcommand=scroll.set)
    name_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.config(command=name_list.yview)

    taken = {n.lower() for n in NAMES_IN_USE}
    for option in ALLOWED_NAME_OPTIONS:
        if option.lower() == name.lower():
            name_list.insert(tk.END, f"{option}  (current)")
            name_list.itemconfig(tk.END, fg="#A0A0A0", selectforeground="#A0A0A0")
        elif option.lower() in taken:
            name_list.insert(tk.END, f"{option}  (in use)")
            name_list.itemconfig(tk.END, fg="#A0A0A0", selectforeground="#A0A0A0")
        else:
            name_list.insert(tk.END, option)

    def confirm_name():
        selection = name_list.curselection()
        if not selection:
            return
        new_name = ALLOWED_NAME_OPTIONS[selection[0]]
        send_packet(server, {"type": "name_change", "name": new_name})
        picker_win.destroy()

    name_list.bind("<Double-Button-1>", lambda event: confirm_name())
    tk.Button(picker_win, text="Confirm", bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 10, "bold"), bd=0, command=confirm_name).pack(fill=tk.X, padx=20, pady=12)


def update_window_title(new_name):
    """Dynamically sets current user profile display on the application header bar."""
    global name
    name = new_name
    window.title(f"Chat Room - @{name}")


def update_room_members_gui():
    """Rebuilds listed items in the active directory pane listbox (No statuses shown)."""
    peers_listbox.delete(0, tk.END)
    peers_listbox.insert(tk.END, "  CONNECTED USERS")
    for m in room_members:
        peers_listbox.insert(tk.END, f"    {m['name']}")


def on_closing():
    """Closes all network sockets cleanly upon termination request."""
    try:
        server.close()
    except Exception:
        pass
    window.destroy()


def auto_scale_client_font(event):
    """Dynamically scales the chat log text font size when the window is resized."""
    if event.widget == window:
        # Scale factor based on baseline dimensions 820x550
        scale = min(window.winfo_width() / 820, window.winfo_height() / 550)
        new_size = max(6, min(16, int(10 * scale)))
        chat_log.configure(font=("Segoe UI", new_size))
        
        # Adjust markdown parsing font styles to match the base size
        chat_log.tag_config("bold_tag", font=("Segoe UI", new_size, "bold"))
        chat_log.tag_config("italic_tag", font=("Segoe UI", new_size, "italic"))
        chat_log.tag_config("code_tag", font=("Courier New", max(5, int(new_size))))


def fetch_name_options():
    """Asks the server for its list of usernames and which ones are in use."""
    global ALLOWED_NAME_OPTIONS, NAMES_IN_USE
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect((server_ip, server_port))
        send_packet(sock, {"type": "get_names"})
        response = recv_packet(sock)
    finally:
        sock.close()
    if not response or response.get("type") != "name_list":
        raise ConnectionError("Server did not send a name list.")
    ALLOWED_NAME_OPTIONS = response.get("names", [])
    NAMES_IN_USE = response.get("taken", [])


def refresh_name_picker():
    """Downloads the latest name list from the server and redraws the picker."""
    try:
        fetch_name_options()
    except Exception as e:
        registration_status.set(f"Could not load names from server: {e}")
        return
    taken = {n.lower() for n in NAMES_IN_USE}
    username_picker.delete(0, tk.END)
    for option in ALLOWED_NAME_OPTIONS:
        if option.lower() in taken:
            username_picker.insert(tk.END, f"{option}  (in use)")
            username_picker.itemconfig(tk.END, fg="#A0A0A0", selectforeground="#A0A0A0")
        else:
            username_picker.insert(tk.END, option)
    registration_status.set("" if ALLOWED_NAME_OPTIONS else "The server has no usernames set up.")


def get_selected_name():
    """Returns the name highlighted in the picker, or an empty string."""
    selection = username_picker.curselection()
    if not selection:
        return ""
    return ALLOWED_NAME_OPTIONS[selection[0]]


# ============================================================
# APP INITIALIZATION
# ============================================================

try:
    server_ip, server_port = find_server()
except Exception as e:
    print(f"Network Chat lookup failed: {e}")
    exit()

server = None

# Profile Setup Layout
reg_win = tk.Tk()
reg_win.title("Register Chat Profile")
reg_win.geometry("340x420")
reg_win.configure(bg=BG_MAIN)
reg_win.resizable(False, False)

tk.Label(reg_win, text="PROFILE SETUP", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 12, "bold")).pack(pady=15)

tk.Label(reg_win, text="Pick your username:", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack()
picker_frame = tk.Frame(reg_win, bg=BG_MAIN)
picker_frame.pack(pady=5, fill=tk.BOTH, expand=True, padx=20)
picker_scroll = tk.Scrollbar(picker_frame)
picker_scroll.pack(side=tk.RIGHT, fill=tk.Y)
username_picker = tk.Listbox(picker_frame, bg=BG_BOX, fg=FG_TEXT, font=("Segoe UI", 10), justify=tk.CENTER, bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, selectbackground=ACCENT_BLUE, selectforeground="white", activestyle="none", exportselection=False, yscrollcommand=picker_scroll.set)
username_picker.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
picker_scroll.config(command=username_picker.yview)


registration_status = tk.StringVar(value="")
status_label = tk.Label(reg_win, textvariable=registration_status, bg=BG_MAIN, fg=ACCENT_RED, font=("Segoe UI", 8, "bold"), wraplength=300, justify=tk.CENTER)
status_label.pack(pady=(0, 3))

button_frame = tk.Frame(reg_win, bg=BG_MAIN)
button_frame.pack(fill=tk.X, padx=20, pady=(4, 12))


def register_profile():
    global name
    global server
    entered = get_selected_name()
    if entered:
        trial_server = None
        try:
            trial_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            trial_server.connect((server_ip, server_port))
            send_packet(trial_server, {
                "type": "handshake",
                "name": entered,
                "username": WINDOWS_USER,
                "hash": calculate_file_hash()
            })
            response = recv_packet(trial_server)
        except Exception as e:
            if trial_server:
                try:
                    trial_server.close()
                except Exception:
                    pass
            messagebox.showerror("Connection Error", f"Could not register profile: {e}")
            return

        if response and response.get("type") == "handshake_ok":
            registration_status.set("")
            name = entered
            server = trial_server
            reg_win.destroy()
            return

        if response and response.get("type") == "name_taken":
            reason = response.get("reason", "taken")
            if reason == "not_allowed" and response.get("allowed"):
                allowed = ", ".join(response.get("allowed", []))
                registration_status.set(f"That name is not in the approved list. Allowed names: {allowed}")
            elif reason == "taken":
                registration_status.set(f"@{entered} is already in use. Pick another name.")
                refresh_name_picker()
            else:
                registration_status.set(f"Registration rejected: {reason}.")
        elif response and response.get("type") == "name_rejected":
            reason = response.get("reason", "blocked")
            if reason == "empty":
                registration_status.set("Username cannot be empty.")
            else:
                registration_status.set("That username cannot be used.")
        elif response and response.get("type") == "reject_integrity":
            registration_status.set("This client code is not approved by the server.")
        else:
            registration_status.set("Could not connect. Please try again.")

        if trial_server:
            try:
                trial_server.close()
            except Exception:
                pass
    else:
        registration_status.set("Pick a username from the list.")


tk.Button(button_frame, text="Connect", bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 10, "bold"), bd=0, width=22, command=register_profile).pack(fill=tk.X)
tk.Button(button_frame, text="Refresh List", bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 8, "bold"), bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, command=refresh_name_picker).pack(fill=tk.X, pady=(6, 0))
username_picker.bind("<Double-Button-1>", lambda event: register_profile())
refresh_name_picker()
reg_win.mainloop()

if not name:
    if server:
        server.close()
    exit()


# ============================================================
# MAIN INTERFACE (Clean White Theme & Inline Layout)
# ============================================================

window = tk.Tk()
window.title(f"Chat Room - @{name}")
window.geometry("820x550")
window.configure(bg=BG_MAIN)

# Left Column: Sidebar Controls (Configured as Light Box area)
sidebar = tk.Frame(window, bg=BG_MAIN, width=180)
sidebar.pack(side=tk.LEFT, fill=tk.Y)
sidebar.pack_propagate(False)

# Separated control area header
control_area = tk.LabelFrame(sidebar, text="ACTIONS", bg=BG_BOX, fg=ACCENT_BLUE, bd=1, relief=tk.SOLID, font=("Segoe UI", 9, "bold"))
control_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Sidebar action buttons. A small helper keeps them all styled the same way.
def make_sidebar_button(text, command):
    btn = tk.Button(control_area, text=text, command=command,
                    bg=BG_MAIN, fg=FG_TEXT, font=("Segoe UI", 9, "bold"),
                    bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR,
                    activebackground=ACCENT_BLUE, activeforeground="white",
                    cursor="hand2")
    btn.pack(fill=tk.X, padx=10, pady=4, ipady=3)
    return btn

btn_name = make_sidebar_button("Change Name", request_name_change)
btn_file = make_sidebar_button("Upload File", send_file_dialog)
btn_paste = make_sidebar_button("Paste Image", paste_image_to_chat)

# User profile card footer
user_footer = tk.Frame(control_area, bg=ACCENT_BLUE, height=56)
user_footer.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
user_footer.pack_propagate(False)

tk.Label(user_footer, text="LOGGED IN AS", font=("Segoe UI", 7, "bold"), bg=ACCENT_BLUE, fg="#D6E4FF").pack(anchor=tk.W, padx=10, pady=(8, 0))
lbl_footer_name = tk.Label(user_footer, text=name, font=("Segoe UI", 11, "bold"), bg=ACCENT_BLUE, fg="white", justify=tk.LEFT)
lbl_footer_name.pack(anchor=tk.W, padx=10)


# Right Column: Active Members List (Segmented Light Box)
right_sidebar = tk.Frame(window, bg=BG_MAIN, width=180)
right_sidebar.pack(side=tk.RIGHT, fill=tk.Y)
right_sidebar.pack_propagate(False)

members_area = tk.LabelFrame(right_sidebar, text="MEMBERS", bg=BG_BOX, fg=ACCENT_BLUE, bd=1, relief=tk.SOLID, font=("Segoe UI", 8, "bold"))
members_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

peers_listbox = tk.Listbox(members_area, bg=BG_BOX, fg=FG_TEXT, selectbackground=ACCENT_BLUE, bd=0, highlightthickness=0, font=("Segoe UI", 9))
peers_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Bind left double-click and right-click to launch dynamic context menus directly on usernames
peers_listbox.bind("<Double-Button-1>", show_peer_context_menu)
peers_listbox.bind("<Button-3>", show_peer_context_menu) # Windows right click
peers_listbox.bind("<Button-2>", show_peer_context_menu) # macOS right click
peer_tooltip = PeerTooltip(peers_listbox)
peers_listbox.bind("<Motion>", on_peer_list_motion)
peers_listbox.bind("<Leave>", lambda e: peer_tooltip.hide_tip())


# Center Section: Chat Logger Interface (Main structured Light Box Area)
chat_container = tk.Frame(window, bg=BG_MAIN)
chat_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

chat_area = tk.LabelFrame(chat_container, text="Global Lobby Chat", bg=BG_BOX, fg=ACCENT_BLUE, bd=1, relief=tk.SOLID, font=("Segoe UI", 10, "bold"))
chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Message Log Box (Pure Light Box scroll section)
chat_log = tk.Text(chat_area, state=tk.DISABLED, wrap=tk.WORD, bg=BG_BOX, fg=FG_TEXT, insertbackground="black", font=("Segoe UI", 10), bd=0)
chat_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Formatting Styles
chat_log.tag_config("timestamp_tag", foreground="#8A8D91")
chat_log.tag_config("system_tag", foreground="#2E7D32", font=("Segoe UI", 9, "italic"))
chat_log.tag_config("role_badge_tag", foreground="#65676B", font=("Segoe UI", 8, "italic"))
chat_log.tag_config("member_tag", foreground="#1C1E21", font=("Segoe UI", 10, "bold"))
chat_log.tag_config("own_member_tag", foreground=ACCENT_BLUE, font=("Segoe UI", 10, "bold")) # Own username highlighted in blue on left
chat_log.tag_config("msg_tag", foreground=FG_TEXT)
chat_log.tag_config("dm_received_tag", foreground="#8E24AA", font=("Segoe UI", 10, "bold", "italic")) # Distinct received Private tag & color
chat_log.tag_config("dm_sent_tag", foreground="#0072C6", font=("Segoe UI", 10, "bold", "italic")) # Distinct sent Private tag & color
chat_log.tag_config("file_tag", foreground=ACCENT_BLUE, font=("Segoe UI", 10, "bold"))

# Basic Markdown Inline Styles
chat_log.tag_config("bold_tag", font=("Segoe UI", 10, "bold"), foreground="#000000")
chat_log.tag_config("italic_tag", font=("Segoe UI", 10, "italic"), foreground=FG_TEXT)
chat_log.tag_config("underline_tag", underline=True, foreground=FG_TEXT)
chat_log.tag_config("strike_tag", overstrike=True, foreground="#8A8D91")
chat_log.tag_config("code_tag", font=("Courier New", 10), background="#EAEAEA", foreground=ACCENT_RED)

new_msg_button = tk.Button(chat_area, text="New message received. Click to scroll down.", bg=ACCENT_BLUE, fg="white", bd=0, font=("Segoe UI", 9, "bold"), command=scroll_to_bottom)

# Input container area (Stark Box)
bottom_frame = tk.Frame(chat_area, bg=BG_BOX)
bottom_frame.pack(fill=tk.X, padx=10, pady=10)

message_input = tk.Entry(bottom_frame, bg="#FFFFFF", fg=FG_TEXT, insertbackground="black", bd=0, highlightthickness=1, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_BLUE, font=("Segoe UI", 11))
message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
message_input.focus()
# Ctrl+V pastes a clipboard image into the chat; plain text paste still works.
message_input.bind("<Control-v>", paste_image_to_chat)

send_button = tk.Button(bottom_frame, text="Send", command=send_message, bg=ACCENT_BLUE, fg="white", font=("Segoe UI", 10, "bold"), bd=0, width=8, cursor="hand2")
send_button.pack(side=tk.RIGHT, padx=(5, 0))

window.minsize(760, 480)
window.bind("<Return>", send_message)
window.bind("<Configure>", auto_scale_client_font) # Scale font when client window resizes
window.protocol("WM_DELETE_WINDOW", on_closing)

receive_thread = threading.Thread(target=receive_messages, daemon=True)
receive_thread.start()

window.mainloop()
