from PyQt6.QtCore import QObject, pyqtSignal

class AppState(QObject):
    # Signals
    on_telemetry_updated = pyqtSignal(dict)
    on_notification = pyqtSignal(str, str) # priority, message
    on_focus_mode_changed = pyqtSignal(bool)
    on_theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.latest_state = {
            "fatigue": 0.0,
            "burnout": 0.0,
            "category": "Unknown",
            "app": "Unknown",
            "hour": 12
        }
        self.focus_active = False

    def update_telemetry(self, data: dict):
        self.latest_state.update(data)
        self.on_telemetry_updated.emit(data)

    def notify(self, priority: str, message: str):
        from storage.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notifications (priority, message) VALUES (?, ?)", (priority, message))
        conn.commit()
        conn.close()
        
        self.on_notification.emit(priority, message)

    def set_focus_mode(self, active: bool):
        self.focus_active = active
        self.on_focus_mode_changed.emit(active)

# Global AppState instance
# While we avoid generic global vars, a Singleton State Manager is standard pattern
state_manager = AppState()
