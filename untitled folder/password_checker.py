import tkinter as tk
from tkinter import font as tkfont
import random
import math

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


# ---- window --------------------------------------------------------------
window = tk.Tk()
window.title("Password Strength Checker")
window.geometry("460x820")
window.minsize(420, 760)
window.configure(bg=BG)

show_password_var = tk.BooleanVar(value=False)
gen_length_var = tk.IntVar(value=12)

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


# ---- header --------------------------------------------------------------
header = tk.Frame(window, bg=BG)
header.pack(fill="x", padx=36, pady=(36, 4))

tk.Label(header, text="Password Strength", font=font_title,
         fg=TEXT, bg=BG, anchor="w").pack(anchor="w")
tk.Label(header, text="Check locally. Nothing leaves this window.",
         font=font_small, fg=TEXT_DIM, bg=BG, anchor="w").pack(anchor="w", pady=(2, 0))

hairline(window)

# ---- input row -----------------------------------------------------------
input_wrap = tk.Frame(window, bg=BG)
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

# ---- generator length slider -------------------------------------------
gen_row = tk.Frame(window, bg=BG)
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
button_row = tk.Frame(window, bg=BG)
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

hairline(window)

# ---- strength bar ------------------------------------------------------
strength_section = tk.Frame(window, bg=BG)
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
hairline(window)

criteria_section = tk.Frame(window, bg=BG)
criteria_section.pack(fill="x", padx=36)
tk.Label(criteria_section, text="Criteria", font=font_body_b, fg=TEXT,
         bg=BG, anchor="w").pack(anchor="w", pady=(0, 8))

crit_length  = Criterion(criteria_section, "At least 8 characters")
crit_upper   = Criterion(criteria_section, "Uppercase letter")
crit_lower   = Criterion(criteria_section, "Lowercase letter")
crit_number  = Criterion(criteria_section, "Number")
crit_symbol  = Criterion(criteria_section, "Special character")

# ---- suggestions -------------------------------------------------------
hairline(window)

suggestion_section = tk.Frame(window, bg=BG)
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

window.mainloop()
