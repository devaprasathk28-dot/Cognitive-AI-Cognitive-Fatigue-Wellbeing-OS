import time
from datetime import datetime

from monitor.notification_engine import show_notification

# ======================================================
# BREAK ENFORCEMENT ENGINE
# ======================================================

def start_break(duration_minutes=5):

    print(f"\n🛑 Break Started for {duration_minutes} minutes\n")

    show_notification(
        "🛑 Break Time",
        f"Take a {duration_minutes}-minute break now"
    )

    total_seconds = duration_minutes * 60

    for remaining in range(total_seconds, 0, -1):

        mins = remaining // 60
        secs = remaining % 60

        print(f"⏳ Break Time Left: {mins:02d}:{secs:02d}", end="\r")

        # Notify every minute
        if remaining % 60 == 0:
            show_notification(
                "⏳ Break Running",
                f"{mins} minutes remaining"
            )

        time.sleep(1)

    print("\n✅ Break Completed\n")

    show_notification(
        "✅ Break Over",
        "You're good to resume work"
    )