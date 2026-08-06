import tkinter as tk
import tkinter.font as tkfont
import random

window = tk.Tk()
window.title("Password Strength Checker")
window.geometry("1019x1200")
window.configure(bg="#0b4763")

show_password_var = tk.BooleanVar(value=False)

available_fonts = tkfont.families()
if "Southern Backroads Script Demo" in available_fonts:
    header_family = "Southern Backroads Script Demo"
elif "Brush Script MT" in available_fonts:
    header_family = "Brush Script MT"
else:
    header_family = "Arial Black"
header_font = tkfont.Font(family=header_family, size=44, weight="bold")


def toggle_password():
    if show_password_var.get():
        password_entry.config(show="")
    else:
        password_entry.config(show="*")


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
    if any(c in "!@#$%^&*()-_=+[]{};:'\",.<>/?\\|`~" for c in password):
        score += 2
    return score


def get_suggestions(password):
    suggestions = []
    if len(password) < 8:
        suggestions.append("Make the password at least 8 characters long.")
    if password and password.islower():
        suggestions.append("Add an uppercase letter.")
    if password and password.isupper():
        suggestions.append("Add a lowercase letter.")
    if not any(char.isdigit() for char in password):
        suggestions.append("Add a number.")
    if not any(char in "!@#$%^&*()-_=+[]{};:'\",.<>/?\\|`~" for char in password):
        suggestions.append("Add a special character.")
    if " " in password:
        suggestions.append("Do not use spaces.")
    common = ["password", "123456", "qwerty", "admin"]
    if password.lower() in common:
        suggestions.append("Avoid using a common password.")
    if "aaa" in password or "111" in password:
        suggestions.append("Avoid repeated characters.")
    if "123" in password or "456" in password or "789" in password:
        suggestions.append("Avoid sequential numbers.")
    if len(password) > 0 and password[0].isdigit():
        suggestions.append("Avoid starting with a number.")
    if len(password) > 0 and password[-1].isdigit():
        suggestions.append("Avoid ending with a number.")
    if len(password) > 20:
        suggestions.append("Password is very long.")
    return suggestions 

def generate_password():
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = "0123456789"
    symbols = "!@#$%^&*"

    password = ""
    for i in range(6):
        password += random.choice(letters)
    for i in range(3):
        password += random.choice(numbers)
    for i in range(3):
        password += random.choice(symbols)

    return password

def check_password(event=None):
    password = password_entry.get()

    # length indicator
    if len(password) >= 8:
        length_label.config(text="✓ At least 8 characters", fg="#800000")
    else:
        length_label.config(text="✗ At least 8 characters", fg="#800000")

    # rating
    score = calculate_score(password)
    if score <= 2:
        rating = "Very Weak"
        rating_color = "#ff4d4d"
    elif score <= 4:
        rating = "Weak"
        rating_color = "#ff4d4d"
    elif score <= 6:
        rating = "Medium"
        rating_color = "#ffcc00"
    elif score <= 8:
        rating = "Strong"
        rating_color = "#90ee90"
    else:
        rating = "Very Strong"
        rating_color = "#00ff00"

    rating_label.config(text=f"Password Rating: {rating}", fg="#800000", font=("Arial", 16, "bold"))

    if not length_label.winfo_ismapped():
        length_label.pack(pady=5)
    if not rating_label.winfo_ismapped():
        rating_label.pack(pady=5)

    # suggestions with prefix and bullets
    if not suggestion_frame.winfo_ismapped():
        suggestion_frame.pack(pady=(10, 0), padx=40)
    suggestions = get_suggestions(password)

    suggestion_heading_label.config(text="Suggestions:", fg="#ff69b4", font=("Arial", 16, "bold"))
    if suggestions:
        suggestion_text = "\n".join(f"• {s}" for s in suggestions)
        suggestion_body_label.config(text=suggestion_text, fg="#ff69b4", font=("Arial", 14, "italic"), justify="left")
    else:
        suggestion_body_label.config(text="• Your password is good!", fg="#90ee90", font=("Arial", 14, "italic"), justify="left")


# UI layout
title = tk.Label(
    window,
    text="Password Strength Checker",
    font=header_font,
    fg="#94cdff",
    bg=window["bg"],
    bd=0,
    highlightthickness=0,
    relief="flat"
)
title.pack(pady=(40, 10))

password_frame = tk.Frame(window, bg=window["bg"])
password_frame.pack(pady=10)

password_entry = tk.Entry(
    password_frame,
    width=40,
    show="*",
    bg="white",
    fg="black",
    insertbackground="black",
    highlightthickness=1,
    highlightbackground="#888",
    highlightcolor="#555"
)
password_entry.pack(side="left", padx=(0, 10))

show_password_checkbox = tk.Checkbutton(
    password_frame,
    text="Show Password",
    variable=show_password_var,
    command=toggle_password,
    bg="#93d8f9",
    fg="black",
    selectcolor="#93d8f9",
    activebackground="#93d8f9"
)
show_password_checkbox.pack(side="left")

button = tk.Button(
    window,
    text="Check Password",
    command=check_password,
    bg="#ffd1dc",
    fg="#8b004b",
    activebackground="#dddddd",
    padx=10,
    pady=5
)
button.pack(pady=6)


def fill_generated_password():
    password = generate_password()
    password_entry.delete(0, tk.END)
    password_entry.insert(0, password)
    check_password()

generate_button = tk.Button(
    window,
    text="Generate Password",
    command=fill_generated_password,
    bg="#ffd1dc",
    fg="#8b004b",
    activebackground="#ffc0cb",
    padx=10,
    pady=5
)
generate_button.pack(pady=6)

length_label = tk.Label(
    window,
    text="",
    font=("Arial", 12),
    fg="#800000",
    bg="#93d8f9"
)

result = tk.Label(
    window,
    text="",
    font=("Times New Roman", 14, "bold italic"),
    fg="black",
)

rating_label = tk.Label(
    window,
    text="",
    font=("Times New Roman", 14, "bold"),
    fg="#800000",
    bg="#93d8f9"
)

suggestion_frame = tk.Frame(
    window,
    bg=window["bg"],
    bd=0,
    relief="flat",
    padx=20,
    pady=20
)

suggestion_heading_label = tk.Label(
    suggestion_frame,
    text="",
    font=("Times New Roman", 16, "bold"),
    fg="#ff4fa3",
    bg=window["bg"],
    justify="left",
    anchor="w"
)
suggestion_heading_label.pack(anchor="w")

suggestion_body_label = tk.Label(
    suggestion_frame,
    text="",
    font=("Arial", 14, "italic"),
    fg="#ff69b4",
    bg=window["bg"],
    justify="left",
    anchor="w",
    wraplength=600
)
suggestion_body_label.pack(anchor="w", pady=(8, 0))

window.mainloop()

