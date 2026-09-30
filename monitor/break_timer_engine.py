# ======================================================
# BREAK ENFORCEMENT TIMER
# STEP-2.18
# ======================================================

import threading
import time
import tkinter as tk

BREAK_ACTIVE = False


def start_break_timer(duration_minutes: int, urgency: str = "Medium"):
    global BREAK_ACTIVE

    if BREAK_ACTIVE:
        return

    BREAK_ACTIVE = True

    seconds = duration_minutes * 60

    def run_timer():
        root = tk.Tk()
        root.title("AI Recovery Break")

        # Always on top
        root.attributes("-topmost", True)
        root.attributes("-fullscreen", True)
        root.configure(bg="#111111")

        label_title = tk.Label(
            root,
            text="🧠 Cognitive Recovery Break",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#111111"
        )
        label_title.pack(pady=10)

        urgency_color = {
            "Low": "#4CAF50",
            "Medium": "#FFC107",
            "High": "#FF5722",
            "Critical": "#FF0000"
        }.get(urgency, "#FFFFFF")

        label_urgency = tk.Label(
            root,
            text=f"Urgency: {urgency}",
            font=("Arial", 12),
            fg=urgency_color,
            bg="#111111"
        )
        label_urgency.pack()

        countdown_label = tk.Label(
            root,
            text="",
            font=("Arial", 28, "bold"),
            fg="white",
            bg="#111111"
        )
        countdown_label.pack(pady=20)

        def update_timer():
            nonlocal seconds

            if seconds <= 0:
                countdown_label.config(text="Break Complete ✅")
                root.after(2000, root.destroy)
                return

            mins = seconds // 60
            secs = seconds % 60
            countdown_label.config(text=f"{mins:02d}:{secs:02d}")
            seconds -= 1
            root.after(1000, update_timer)

        update_timer()
        root.mainloop()

        global BREAK_ACTIVE
        BREAK_ACTIVE = False

    threading.Thread(target=run_timer).start()
