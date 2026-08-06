import tkinter as tk
import tkinter.font as tkfont

window = tk.Tk()
window.title("Password Strength Checker")
window.geometry("800x600")
window.configure(bg="#222222")

show_password_var = tk.BooleanVar(value=False)

header_font = tkfont.Font(family="Wasteland", size=34, weight="bold")


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


def check_password(event=None):
    password = password_entry.get()

    # length indicator
    if len(password) >= 8:
        length_label.config(text="✓ At least 8 characters", fg="#90ee90")
    else:
        length_label.config(text="✗ At least 8 characters", fg="#ff4d4d")

    # displayed password in bold italic
    result.config(text=password, font=("Arial", 14, "bold italic"), fg="#ffffff")

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

    rating_label.config(text=f"Password Rating: {rating}", fg=rating_color, font=("Arial", 16, "bold"))

    # suggestions with prefix and bullets
    suggestions = get_suggestions(password)
    if suggestions:
        suggestion_text = "Suggestions:\n" + "\n".join(f"• {s}" for s in suggestions)
        suggestion_label.config(text=suggestion_text, fg="#ff69b4", font=("Arial", 12), justify="center")
    else:
        suggestion_label.config(text="Suggestions:\n• Your password is good!", fg="#90ee90", font=("Arial", 12), justify="center")


# UI layout
title = tk.Label(
    window,
    text="Password Strength Checker",
    font=header_font,
    fg="white",
    bg="#222222"
)
title.pack(pady=20)

password_entry = tk.Entry(
    window,
    width=40,
    show="*",
    bg="white",
    fg="black",
    insertbackground="black",
    highlightthickness=1,
    highlightbackground="#888",
    highlightcolor="#555"
)
password_entry.pack(pady=10)

# check button immediately below the entry
button = tk.Button(
    window,
    text="Check Password",
    command=check_password,
    bg="#ffffff",
    fg="#000000",
    activebackground="#dddddd",
    padx=10,
    pady=5
)
button.pack(pady=6)

show_password_checkbox = tk.Checkbutton(
    window,
    text="Show Password",
    variable=show_password_var,
    command=toggle_password,
    bg="#222222",
    fg="white",
    selectcolor="#222222",
    activebackground="#222222"
)
show_password_checkbox.pack(pady=6)

length_label = tk.Label(
    window,
    text="",
    font=("Arial", 12),
    fg="white",
    bg="#222222"
)
length_label.pack(pady=5)

result = tk.Label(
    window,
    text="",
    font=("Arial", 14, "bold italic"),
    fg="#ffffff",
    bg="#222222"
)
result.pack(pady=10)

rating_label = tk.Label(
    window,
    text="",
    font=("Arial", 14, "bold"),
    fg="white",
    bg="#222222"
)
rating_label.pack(pady=5)

suggestion_label = tk.Label(
    window,
    text="",
    font=("Arial", 12),
    fg="#ff69b4",
    bg="#222222",
    justify="center"
)
suggestion_label.pack(pady=5)

window.mainloop()
