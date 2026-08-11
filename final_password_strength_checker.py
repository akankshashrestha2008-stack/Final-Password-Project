import tkinter as tk
from tkinter import font as tkfont
import tkinter.messagebox as messagebox
import random
import math
import json
import os
import hashlib
import secrets
from datetime import datetime

# ---- gradient background helpers ---------------------------------------
def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(c))) for c in rgb)


def _lerp_color(c1, c2, t):
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t))

# ----------------------------------------------------------------------
# PASSWORD STRENGTH CHECKER — minimal dark UI
# ----------------------------------------------------------------------

# ---- palette -----------------------------------------------------------
BG          = "#0B0E14"   # window background
PANEL       = "#12161F"   # entry / card background
BORDER      = "#232837"   # hairline borders
TEXT        = "#F4F6FB"   # primary text
TEXT_DIM    = "#8A90A3"   # secondary text
ACCENT      = "#4F9DFF"   # primary accent (buttons, focus)
ACCENT_DIM  = "#1B2740"   # accent button hover/pressed background
GOOD        = "#5FE3A1"
WARN        = "#FFC65C"
BAD         = "#FF6B6B"

STRENGTH_LEVELS = [
    (2, "Very Weak", BAD),
    (4, "Weak", BAD),
    (6, "Medium", WARN),
    (8, "Strong", GOOD),
    (99, "Very Strong", GOOD),
]

SYMBOLS = "!@#$%^&*()-_=+[]{};:'\",.<>/?\\|`~"

# small offline breach wordlist — exact matches only, everything stays local
COMMON_PASSWORDS = {
    "password", "123456", "123456789", "qwerty", "111111", "12345678",
    "abc123", "password1", "1234567", "12345", "iloveyou", "admin",
    "welcome", "monkey", "login", "letmein", "dragon", "football",
    "starwars", "sunshine", "princess", "qwerty123", "solo", "master",
    "passw0rd", "trustno1", "freedom", "whatever", "qazwsx", "666666",
    "shadow", "123123", "654321", "superman", "michael", "ninja",
    "mustang", "baseball", "access", "flower", "hottie", "loveme",
    "jordan23", "harley", "hunter", "ranger", "buster", "soccer",
}

# guesses/sec for the crack-time estimate — a fast offline attack (GPU rig)
GUESS_RATE = 1e10

# local, encrypted "save this password" vault — lives next to the script,
# never leaves this machine
VAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault.json")
VAULT_LABEL_PLACEHOLDER = "Label (e.g. Gmail) — optional"


# ---- window --------------------------------------------------------------
window = tk.Tk()
window.title("Password Strength Checker")
window.geometry("460x760")
window.minsize(380, 480)
window.configure(bg=BG)

show_password_var = tk.BooleanVar(value=False)
gen_length_var = tk.IntVar(value=12)

# ---- scrollable canvas ---------------------------------------------------
# The whole app lives inside a scrollable canvas so nothing gets clipped
# on smaller screens or when content grows (e.g. the vault row, breach
# warnings). The gradient background is drawn directly on this canvas so
# it scrolls along with the content instead of staying fixed.
outer = tk.Frame(window, bg=BG)
outer.pack(fill="both", expand=True)

scroll_canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, bd=0)
scrollbar = tk.Scrollbar(outer, orient="vertical", command=scroll_canvas.yview)
scroll_canvas.configure(yscrollcommand=scrollbar.set)
scroll_canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

content = tk.Frame(scroll_canvas, bg=BG)
content_window_id = scroll_canvas.create_window((0, 0), window=content, anchor="nw")


def _sync_content_width(event):
    scroll_canvas.itemconfig(content_window_id, width=event.width)


scroll_canvas.bind("<Configure>", _sync_content_width)


def _on_mousewheel(event):
    if getattr(event, "num", None) == 4:
        scroll_canvas.yview_scroll(-1, "units")
    elif getattr(event, "num", None) == 5:
        scroll_canvas.yview_scroll(1, "units")
    else:
        delta = event.delta
        if abs(delta) >= 120:
            delta = delta / 120
        scroll_canvas.yview_scroll(int(-1 * delta), "units")


scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)   # Windows / macOS
scroll_canvas.bind_all("<Button-4>", _on_mousewheel)      # Linux scroll up
scroll_canvas.bind_all("<Button-5>", _on_mousewheel)      # Linux scroll down

# ---- ambient gradient background ---------------------------------------
# A soft vertical gradient with two subtle "glow" blobs (blue + purple),
# reminiscent of the aurora background used in the project's keynote deck.
# Drawn directly on scroll_canvas, sized to the full scrollable content
# height (not just the visible window), so it scrolls naturally.
GRAD_TOP    = "#070910"
GRAD_MID    = "#0C1120"
GRAD_BOTTOM = "#15122A"
GLOW_BLUE   = "#2C5FA8"
GLOW_PURPLE = "#4A3A8F"

_bg_redraw_job = None


def _draw_gradient_background(event=None):
    w = scroll_canvas.winfo_width()
    h = max(scroll_canvas.winfo_height(), content.winfo_reqheight())
    if w < 2 or h < 2:
        return
    scroll_canvas.delete("gradient")

    step = 4
    for y in range(0, h, step):
        t = y / h
        if t < 0.5:
            color = _lerp_color(GRAD_TOP, GRAD_MID, t / 0.5)
        else:
            color = _lerp_color(GRAD_MID, GRAD_BOTTOM, (t - 0.5) / 0.5)
        scroll_canvas.create_rectangle(0, y, w, y + step, fill=color, outline="", tags="gradient")

    def glow(cx, cy, radius, color, base_t):
        base_color = _lerp_color(GRAD_TOP, GRAD_BOTTOM, base_t)
        steps = 18
        for i in range(steps, 0, -1):
            t = i / steps
            r = radius * t
            blend = _lerp_color(base_color, color, (1 - t) * 0.55)
            scroll_canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                       fill=blend, outline="", tags="gradient")

    glow(w * 0.82, h * 0.05, max(w, h) * 0.4, GLOW_BLUE, 0.05)
    glow(w * 0.1, h * 0.97, max(w, h) * 0.42, GLOW_PURPLE, 0.9)

    scroll_canvas.tag_lower("gradient")
    scroll_canvas.configure(scrollregion=(0, 0, w, h))


def _schedule_bg_redraw(event=None):
    global _bg_redraw_job
    if _bg_redraw_job is not None:
        window.after_cancel(_bg_redraw_job)
    _bg_redraw_job = window.after(40, _draw_gradient_background)


scroll_canvas.bind("<Configure>", _schedule_bg_redraw, add="+")
content.bind("<Configure>", _schedule_bg_redraw, add="+")

# ---- fonts -----------------------------------------------------------
available_fonts = tkfont.families()
base_family = "SF Pro Display" if "SF Pro Display" in available_fonts else \
              ("Segoe UI" if "Segoe UI" in available_fonts else "Helvetica")

font_title    = tkfont.Font(family=base_family, size=19, weight="bold")
font_body     = tkfont.Font(family=base_family, size=11)
font_body_b   = tkfont.Font(family=base_family, size=11, weight="bold")
font_small    = tkfont.Font(family=base_family, size=9)
font_entry    = tkfont.Font(family="Menlo" if "Menlo" in available_fonts else "Consolas",
                             size=13)
font_rating   = tkfont.Font(family=base_family, size=13, weight="bold")


# ---- logic (unchanged behaviour) --------------------------------------
def calculate_score(password):
    score = 0
    if len(password) >= 8:
        score += 2
    if len(password) >= 12:
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in SYMBOLS for c in password):
        score += 2
    return score


def get_suggestions(password):
    suggestions = []
    if len(password) < 8:
        suggestions.append("Use at least 8 characters")
    if password and password.islower():
        suggestions.append("Add an uppercase letter")
    if password and password.isupper():
        suggestions.append("Add a lowercase letter")
    if not any(c.isdigit() for c in password):
        suggestions.append("Add a number")
    if not any(c in SYMBOLS for c in password):
        suggestions.append("Add a special character")
    if " " in password:
        suggestions.append("Remove spaces")
    if password.lower() in COMMON_PASSWORDS:
        suggestions.append("Avoid common passwords")
    if "aaa" in password or "111" in password:
        suggestions.append("Avoid repeated characters")
    if any(seq in password for seq in ("123", "456", "789")):
        suggestions.append("Avoid sequential numbers")
    if password and password[0].isdigit():
        suggestions.append("Avoid starting with a number")
    if password and password[-1].isdigit():
        suggestions.append("Avoid ending with a number")
    return suggestions


def generate_password(length=12):
    letters_lower = "abcdefghijklmnopqrstuvwxyz"
    letters_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = "0123456789"
    symbols = "!@#$%^&*"

    length = max(6, length)
    # guarantee at least one of each character class, fill the rest randomly
    pw = [
        random.choice(letters_lower),
        random.choice(letters_upper),
        random.choice(numbers),
        random.choice(symbols),
    ]
    pool = letters_lower + letters_upper + numbers + symbols
    pw += [random.choice(pool) for _ in range(length - len(pw))]
    random.shuffle(pw)
    return "".join(pw)


def rating_for(score):
    for threshold, label, color in STRENGTH_LEVELS:
        if score <= threshold:
            return label, color
    return STRENGTH_LEVELS[-1][1], STRENGTH_LEVELS[-1][2]


def charset_size(password):
    size = 0
    if any(c.islower() for c in password):
        size += 26
    if any(c.isupper() for c in password):
        size += 26
    if any(c.isdigit() for c in password):
        size += 10
    if any(c in SYMBOLS for c in password):
        size += len(SYMBOLS)
    if any(c == " " for c in password):
        size += 1
    return size


def calculate_entropy(password):
    """Bits of entropy, assuming a random password drawn from the
    character classes present. Not a measure of true randomness for
    human-chosen passwords, but a standard, explainable estimate."""
    size = charset_size(password)
    if size == 0 or not password:
        return 0.0
    return len(password) * math.log2(size)


def format_duration(seconds):
    if seconds < 1:
        return "instantly"
    units = [
        ("century", 60 * 60 * 24 * 365 * 100),
        ("year", 60 * 60 * 24 * 365),
        ("day", 60 * 60 * 24),
        ("hour", 60 * 60),
        ("minute", 60),
        ("second", 1),
    ]
    for name, unit_seconds in units:
        value = seconds / unit_seconds
        if value >= 1:
            value = int(value)
            if value > 999_999_999:
                return "trillions of centuries"
            plural = "" if value == 1 else "s"
            return f"~{value:,} {name}{plural}"
    return "instantly"


def estimate_crack_time(password):
    entropy = calculate_entropy(password)
    if entropy == 0:
        return "instantly", entropy
    combinations = 2 ** entropy
    seconds = (combinations / 2) / GUESS_RATE   # average case: half the keyspace
    return format_duration(seconds), entropy


# ---- small reusable widgets --------------------------------------------
def hairline(parent):
    line = tk.Frame(parent, bg=BORDER, height=1)
    line.pack(fill="x", pady=(18, 18))
    return line


class Criterion:
    """A single checklist row: dot + label, toggled met/unmet."""
    def __init__(self, parent, text):
        self.row = tk.Frame(parent, bg=BG)
        self.row.pack(fill="x", pady=3)
        self.dot = tk.Canvas(self.row, width=10, height=10, bg=BG,
                              highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 10))
        self.dot_id = self.dot.create_oval(1, 1, 9, 9, fill=BORDER, outline="")
        self.label = tk.Label(self.row, text=text, font=font_body,
                               fg=TEXT_DIM, bg=BG, anchor="w")
        self.label.pack(side="left")

    def set_met(self, met):
        color = GOOD if met else BORDER
        self.dot.itemconfig(self.dot_id, fill=color)
        self.label.config(fg=TEXT if met else TEXT_DIM)


def styled_button(parent, text, command, primary=False):
    bg = ACCENT if primary else PANEL
    fg = "#04101F" if primary else TEXT
    hover_bg = "#6FB0FF" if primary else ACCENT_DIM
    btn = tk.Label(
        parent, text=text, font=font_body_b, fg=fg, bg=bg,
        padx=14, pady=10, cursor="hand2",
        highlightthickness=0 if primary else 1,
        highlightbackground=BORDER
    )
    btn.bind("<Button-1>", lambda e: command())
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


# ---- local password vault ------------------------------------------------
# Saved passwords are encrypted with a key derived from a master password
# (PBKDF2-HMAC-SHA256) and stored in vault.json next to this script. The
# master password itself is never stored — only a verifier hash of the
# derived key, so it can be checked without ever writing the password
# anywhere. Nothing here ever touches the network.

_session_key = None  # the derived encryption key, kept in memory only


def load_vault():
    if not os.path.exists(VAULT_PATH):
        return None
    try:
        with open(VAULT_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_vault(data):
    with open(VAULT_PATH, "w") as f:
        json.dump(data, f, indent=2)


def derive_key(master_password, salt):
    return hashlib.pbkdf2_hmac("sha256", master_password.encode("utf-8"), salt, 100_000)


def _keystream(key, length):
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += hashlib.sha256(key + counter.to_bytes(4, "big")).digest()
        counter += 1
    return bytes(out[:length])


def vault_encrypt(key, plaintext):
    data = plaintext.encode("utf-8")
    ks = _keystream(key, len(data))
    return bytes(a ^ b for a, b in zip(data, ks)).hex()


def vault_decrypt(key, cipher_hex):
    cipher = bytes.fromhex(cipher_hex)
    ks = _keystream(key, len(cipher))
    return bytes(a ^ b for a, b in zip(cipher, ks)).decode("utf-8")


def _password_prompt(title, subtitle, confirm=False):
    """A small themed modal asking for a master password. Returns the
    entered string, or None if the user cancelled."""
    result = {"value": None}
    dialog = tk.Toplevel(window)
    dialog.title(title)
    dialog.configure(bg=BG)
    dialog.resizable(False, False)
    dialog.transient(window)
    dialog.grab_set()

    tk.Label(dialog, text=title, font=font_body_b, fg=TEXT, bg=BG,
              wraplength=280, justify="left").pack(padx=26, pady=(22, 4), anchor="w")
    tk.Label(dialog, text=subtitle, font=font_small, fg=TEXT_DIM, bg=BG,
              wraplength=280, justify="left").pack(padx=26, anchor="w")

    entry1 = tk.Entry(dialog, show="*", bg=PANEL, fg=TEXT, insertbackground=TEXT,
                       relief="flat", font=font_entry, bd=0, highlightthickness=1,
                       highlightbackground=BORDER, highlightcolor=ACCENT)
    entry1.pack(padx=26, pady=(14, 0), fill="x", ipady=4)

    entry2 = None
    if confirm:
        entry2 = tk.Entry(dialog, show="*", bg=PANEL, fg=TEXT, insertbackground=TEXT,
                           relief="flat", font=font_entry, bd=0, highlightthickness=1,
                           highlightbackground=BORDER, highlightcolor=ACCENT)
        entry2.pack(padx=26, pady=(8, 0), fill="x", ipady=4)

    error_label = tk.Label(dialog, text="", font=font_small, fg=BAD, bg=BG)
    error_label.pack(padx=26, pady=(8, 0), anchor="w")

    def submit(event=None):
        v1 = entry1.get()
        if confirm:
            v2 = entry2.get()
            if len(v1) < 4:
                error_label.config(text="Use at least 4 characters.")
                return
            if v1 != v2:
                error_label.config(text="Passwords don't match.")
                return
        elif not v1:
            error_label.config(text="Master password required.")
            return
        result["value"] = v1
        dialog.destroy()

    def cancel():
        dialog.destroy()

    btn_row = tk.Frame(dialog, bg=BG)
    btn_row.pack(padx=26, pady=(14, 22), fill="x")
    styled_button(btn_row, "Cancel", cancel).pack(side="left", expand=True, fill="x", padx=(0, 6))
    styled_button(btn_row, "Continue", submit, primary=True).pack(side="left", expand=True, fill="x", padx=(6, 0))

    entry1.bind("<Return>", submit)
    if entry2:
        entry2.bind("<Return>", submit)
    entry1.focus_set()

    window.wait_window(dialog)
    return result["value"]


def ensure_vault_unlocked():
    """Returns the active encryption key, prompting to create or unlock
    the vault as needed. Returns None if the user cancels."""
    global _session_key
    if _session_key is not None:
        return _session_key

    vault = load_vault()
    if vault is None:
        pw = _password_prompt(
            "Create a master password",
            "This protects everything you save here. It can't be recovered if lost, so pick something memorable."
            , confirm=True
        )
        if not pw:
            return None
        salt = secrets.token_bytes(16)
        key = derive_key(pw, salt)
        save_vault({"salt": salt.hex(), "verifier": hashlib.sha256(key).hexdigest(), "entries": []})
        _session_key = key
        return key

    while True:
        pw = _password_prompt("Unlock your vault", "Enter your master password to continue.")
        if not pw:
            return None
        salt = bytes.fromhex(vault["salt"])
        key = derive_key(pw, salt)
        if hashlib.sha256(key).hexdigest() == vault["verifier"]:
            _session_key = key
            return key
        messagebox.showerror("Incorrect password", "That master password doesn't match. Try again.")


def update_vault_count():
    vault = load_vault()
    count = len(vault["entries"]) if vault and "entries" in vault else 0
    vault_btn.config(text=f"Vault ({count})" if count else "Vault")


def save_current_password():
    password = password_entry.get()
    if not password:
        return
    label = vault_label_entry.get().strip()
    if not label or label == VAULT_LABEL_PLACEHOLDER:
        label = "Untitled"

    key = ensure_vault_unlocked()
    if key is None:
        return

    vault = load_vault() or {"entries": []}
    vault.setdefault("entries", []).append({
        "id": secrets.token_hex(8),
        "label": label,
        "cipher": vault_encrypt(key, password),
        "created": datetime.now().strftime("%b %d, %H:%M"),
    })
    save_vault(vault)

    vault_label_entry.delete(0, tk.END)
    _vault_label_focus_out(None)
    update_vault_count()

    original = save_btn.cget("text")
    save_btn.config(text="Saved")
    window.after(1100, lambda: save_btn.config(text=original))


def render_vault_row(parent, entry, key, host_window):
    row = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
    row.pack(fill="x", pady=6)

    top = tk.Frame(row, bg=PANEL)
    top.pack(fill="x", padx=14, pady=(12, 2))
    tk.Label(top, text=entry["label"], font=font_body_b, fg=TEXT, bg=PANEL, anchor="w").pack(side="left")
    tk.Label(top, text=entry.get("created", ""), font=font_small, fg=TEXT_DIM, bg=PANEL, anchor="e").pack(side="right")

    plaintext = vault_decrypt(key, entry["cipher"])
    pw_var = tk.StringVar(value="•" * len(plaintext))
    tk.Label(row, textvariable=pw_var, font=font_entry, fg=TEXT_DIM, bg=PANEL, anchor="w").pack(
        fill="x", padx=14, pady=(0, 10))

    state = {"revealed": False}

    def toggle_reveal():
        state["revealed"] = not state["revealed"]
        pw_var.set(plaintext if state["revealed"] else "•" * len(plaintext))
        reveal_btn.config(text="Hide" if state["revealed"] else "Show")

    def copy_entry():
        window.clipboard_clear()
        window.clipboard_append(plaintext)
        copy_e_btn.config(text="Copied")
        host_window.after(1000, lambda: copy_e_btn.config(text="Copy"))

    def delete_entry():
        if not messagebox.askyesno("Delete saved password", f"Remove '{entry['label']}' from your vault?"):
            return
        data = load_vault()
        data["entries"] = [e for e in data["entries"] if e["id"] != entry["id"]]
        save_vault(data)
        row.destroy()
        update_vault_count()

    action_row = tk.Frame(row, bg=PANEL)
    action_row.pack(fill="x", padx=14, pady=(0, 12))
    reveal_btn = styled_button(action_row, "Show", toggle_reveal)
    reveal_btn.pack(side="left")
    copy_e_btn = styled_button(action_row, "Copy", copy_entry)
    copy_e_btn.pack(side="left", padx=(8, 0))
    styled_button(action_row, "Delete", delete_entry).pack(side="right")


def open_vault():
    vault = load_vault()
    if vault is None:
        messagebox.showinfo("No saved passwords yet",
                             "Use the Save button next to a password to create your vault.")
        return

    key = ensure_vault_unlocked()
    if key is None:
        return
    vault = load_vault()

    win = tk.Toplevel(window)
    win.title("Saved Passwords")
    win.configure(bg=BG)
    win.geometry("380x480")
    win.minsize(340, 360)
    win.transient(window)

    tk.Label(win, text="Saved Passwords", font=font_title, fg=TEXT, bg=BG).pack(
        anchor="w", padx=24, pady=(22, 2))
    tk.Label(win, text="Encrypted locally with your master password.",
             font=font_small, fg=TEXT_DIM, bg=BG, wraplength=320, justify="left").pack(
        anchor="w", padx=24, pady=(0, 14))

    container = tk.Frame(win, bg=BG)
    container.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    list_frame = tk.Frame(canvas, bg=BG)
    list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=list_frame, anchor="nw", width=310)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    entries = vault.get("entries", [])
    if not entries:
        tk.Label(list_frame, text="No saved passwords yet.", font=font_body,
                  fg=TEXT_DIM, bg=BG).pack(pady=20)
    else:
        for entry in reversed(entries):
            render_vault_row(list_frame, entry, key, win)


# ---- header --------------------------------------------------------------
header = tk.Frame(content, bg=BG)
header.pack(fill="x", padx=36, pady=(36, 4))

header_top = tk.Frame(header, bg=BG)
header_top.pack(fill="x")

tk.Label(header_top, text="Password Strength", font=font_title,
         fg=TEXT, bg=BG, anchor="w").pack(side="left")

vault_btn = styled_button(header_top, "Vault", open_vault)
vault_btn.pack(side="right")

tk.Label(header, text="Check locally. Nothing leaves this window.",
         font=font_small, fg=TEXT_DIM, bg=BG, anchor="w").pack(anchor="w", pady=(8, 0))

hairline(content)

# ---- input row -----------------------------------------------------------
input_wrap = tk.Frame(content, bg=BG)
input_wrap.pack(fill="x", padx=36)

entry_frame = tk.Frame(input_wrap, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER, highlightcolor=ACCENT)
entry_frame.pack(fill="x")

password_entry = tk.Entry(
    entry_frame, show="*", bg=PANEL, fg=TEXT, insertbackground=TEXT,
    relief="flat", font=font_entry, bd=0
)
password_entry.pack(fill="x", padx=14, pady=12)
password_entry.bind("<KeyRelease>", lambda e: check_password())


def toggle_password():
    password_entry.config(show="" if show_password_var.get() else "*")


toggle_row = tk.Frame(input_wrap, bg=BG)
toggle_row.pack(fill="x", pady=(10, 0))

show_password_checkbox = tk.Checkbutton(
    toggle_row, text="Show password", variable=show_password_var,
    command=toggle_password, font=font_small, fg=TEXT_DIM, bg=BG,
    activebackground=BG, activeforeground=TEXT, selectcolor=PANEL,
    highlightthickness=0, bd=0, anchor="w", cursor="hand2"
)
show_password_checkbox.pack(side="left")


def copy_to_clipboard():
    password = password_entry.get()
    if not password:
        return
    window.clipboard_clear()
    window.clipboard_append(password)
    original = copy_btn.cget("text")
    copy_btn.config(text="Copied")
    window.after(1100, lambda: copy_btn.config(text=original))


copy_btn = styled_button(toggle_row, "Copy", copy_to_clipboard)
copy_btn.pack(side="right")

# ---- save this password to the local vault -----------------------------
vault_row = tk.Frame(input_wrap, bg=BG)
vault_row.pack(fill="x", pady=(14, 0))

vault_input_row = tk.Frame(vault_row, bg=BG)
vault_input_row.pack(fill="x")

vault_label_entry = tk.Entry(
    vault_input_row, bg=PANEL, fg=TEXT_DIM, insertbackground=TEXT,
    relief="flat", font=font_body, bd=0, highlightthickness=1,
    highlightbackground=BORDER, highlightcolor=ACCENT
)
vault_label_entry.insert(0, VAULT_LABEL_PLACEHOLDER)
vault_label_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=6)


def _vault_label_focus_in(event):
    if vault_label_entry.get() == VAULT_LABEL_PLACEHOLDER:
        vault_label_entry.delete(0, tk.END)
        vault_label_entry.config(fg=TEXT)


def _vault_label_focus_out(event):
    if not vault_label_entry.get():
        vault_label_entry.insert(0, VAULT_LABEL_PLACEHOLDER)
        vault_label_entry.config(fg=TEXT_DIM)


vault_label_entry.bind("<FocusIn>", _vault_label_focus_in)
vault_label_entry.bind("<FocusOut>", _vault_label_focus_out)

save_btn = styled_button(vault_input_row, "Save", save_current_password)
save_btn.pack(side="right")

# ---- generator length slider -------------------------------------------
gen_row = tk.Frame(content, bg=BG)
gen_row.pack(fill="x", padx=36, pady=(18, 0))

gen_head = tk.Frame(gen_row, bg=BG)
gen_head.pack(fill="x")
tk.Label(gen_head, text="Generator length", font=font_small,
         fg=TEXT_DIM, bg=BG, anchor="w").pack(side="left")
gen_len_label = tk.Label(gen_head, text="12", font=font_small,
                          fg=TEXT_DIM, bg=BG, anchor="e")
gen_len_label.pack(side="right")


def on_length_change(value):
    gen_len_label.config(text=str(int(float(value))))


length_slider = tk.Scale(
    gen_row, from_=8, to=32, orient="horizontal", variable=gen_length_var,
    command=on_length_change, showvalue=False, bg=BG, fg=TEXT_DIM,
    troughcolor=PANEL, highlightthickness=0, bd=0, sliderrelief="flat",
    activebackground=ACCENT
)
length_slider.pack(fill="x", pady=(4, 0))

# ---- buttons ---------------------------------------------------------
button_row = tk.Frame(content, bg=BG)
button_row.pack(fill="x", padx=36, pady=(18, 0))


def fill_generated_password():
    pw = generate_password(gen_length_var.get())
    password_entry.delete(0, tk.END)
    password_entry.insert(0, pw)
    check_password()


check_btn = styled_button(button_row, "Check Password", lambda: check_password(), primary=True)
check_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

generate_btn = styled_button(button_row, "Generate", fill_generated_password)
generate_btn.pack(side="left", expand=True, fill="x", padx=(6, 0))

hairline(content)

# ---- strength bar ------------------------------------------------------
strength_section = tk.Frame(content, bg=BG)
strength_section.pack(fill="x", padx=36)

strength_head = tk.Frame(strength_section, bg=BG)
strength_head.pack(fill="x")
rating_label = tk.Label(strength_head, text="Strength", font=font_rating,
                         fg=TEXT_DIM, bg=BG, anchor="w")
rating_label.pack(side="left")
score_label = tk.Label(strength_head, text="", font=font_small,
                        fg=TEXT_DIM, bg=BG, anchor="e")
score_label.pack(side="right")

bar_track = tk.Frame(strength_section, bg=PANEL, height=8)
bar_track.pack(fill="x", pady=(10, 0))
bar_track.pack_propagate(False)
bar_fill = tk.Frame(bar_track, bg=BORDER, width=0)
bar_fill.place(x=0, y=0, relheight=1, width=0)

meta_row = tk.Frame(strength_section, bg=BG)
meta_row.pack(fill="x", pady=(10, 0))
entropy_label = tk.Label(meta_row, text="", font=font_small, fg=TEXT_DIM,
                          bg=BG, anchor="w", justify="left")
entropy_label.pack(anchor="w")

breach_banner = tk.Frame(strength_section, bg="#2A1414", highlightthickness=1,
                          highlightbackground=BAD)
breach_label = tk.Label(
    breach_banner, text="⚠  This password appears in a common breach list — avoid it.",
    font=font_small, fg=BAD, bg="#2A1414", wraplength=380, justify="left", anchor="w"
)
breach_label.pack(padx=12, pady=8, anchor="w")
# breach_banner is packed/unpacked dynamically inside check_password()

MAX_SCORE = 8

# ---- criteria checklist ---------------------------------------------
hairline(content)

criteria_section = tk.Frame(content, bg=BG)
criteria_section.pack(fill="x", padx=36)
tk.Label(criteria_section, text="Criteria", font=font_body_b, fg=TEXT,
         bg=BG, anchor="w").pack(anchor="w", pady=(0, 8))

crit_length  = Criterion(criteria_section, "At least 8 characters")
crit_upper   = Criterion(criteria_section, "Uppercase letter")
crit_lower   = Criterion(criteria_section, "Lowercase letter")
crit_number  = Criterion(criteria_section, "Number")
crit_symbol  = Criterion(criteria_section, "Special character")

# ---- suggestions -------------------------------------------------------
hairline(content)

suggestion_section = tk.Frame(content, bg=BG)
suggestion_section.pack(fill="x", padx=36, pady=(0, 30))

suggestion_heading_label = tk.Label(
    suggestion_section, text="Suggestions", font=font_body_b,
    fg=TEXT, bg=BG, anchor="w"
)
suggestion_heading_label.pack(anchor="w", pady=(0, 8))

suggestion_body_label = tk.Label(
    suggestion_section, text="Start typing a password above.",
    font=font_body, fg=TEXT_DIM, bg=BG, justify="left", anchor="w",
    wraplength=380
)
suggestion_body_label.pack(anchor="w")

# kept for structural compatibility with earlier layout naming
suggestion_frame = suggestion_section
length_label = tk.Label(window)  # retained, unused visually (info folded into checklist)
result = tk.Label(window)        # retained for compatibility, unused visually


# ---- main handler -------------------------------------------------------
def check_password(event=None):
    password = password_entry.get()
    score = calculate_score(password)
    rating, color = rating_for(score) if password else ("—", TEXT_DIM)

    rating_label.config(text=f"Strength: {rating}", fg=color if password else TEXT_DIM)
    score_label.config(text=f"{min(score, MAX_SCORE)}/{MAX_SCORE}" if password else "")

    # strength bar fill
    track_width = bar_track.winfo_width() or 380
    pct = min(score / MAX_SCORE, 1.0) if password else 0
    bar_fill.place_configure(width=int(track_width * pct))
    bar_fill.config(bg=color if password else BORDER)

    # entropy + crack-time estimate
    if password:
        crack_time, entropy = estimate_crack_time(password)
        entropy_label.config(
            text=f"{entropy:.0f} bits of entropy  ·  est. time to crack: {crack_time}"
        )
    else:
        entropy_label.config(text="")

    # offline breach check
    if password and password.lower() in COMMON_PASSWORDS:
        breach_banner.pack(fill="x", pady=(10, 0))
    else:
        breach_banner.pack_forget()

    # criteria dots
    crit_length.set_met(len(password) >= 8)
    crit_upper.set_met(any(c.isupper() for c in password))
    crit_lower.set_met(any(c.islower() for c in password))
    crit_number.set_met(any(c.isdigit() for c in password))
    crit_symbol.set_met(any(c in SYMBOLS for c in password))

    # suggestions
    suggestions = get_suggestions(password)
    if not password:
        suggestion_body_label.config(text="Start typing a password above.", fg=TEXT_DIM)
    elif suggestions:
        text = "\n".join(f"·  {s}" for s in suggestions)
        suggestion_body_label.config(text=text, fg=TEXT_DIM)
    else:
        suggestion_body_label.config(text="·  Looks good. No issues found.", fg=GOOD)


window.bind("<Configure>", lambda e: check_password())
check_password()
update_vault_count()

window.mainloop()
