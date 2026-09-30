from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QLineEdit, QPushButton, QFrame
from PyQt6.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal

from ui.components.core_ui import create_card_frame, fade_in, animate_scroll_to_bottom
from storage.db import save_chat_message, get_chat_history

class ChatWorker(QObject):
    reply_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            from monitor.ai_companion_engine import ask_ai
            reply = ask_ai(self.prompt)
            self.reply_ready.emit(reply if reply else "No response.")
        except Exception as e:
            self.error.emit(f"AI Error: {e}")

class ChatBubble(QFrame):
    def __init__(self, text: str, is_user: bool):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        bg_color = "#5D5FEF" if is_user else "rgba(255, 255, 255, 0.04)"
        text_color = "#FFFFFF" if is_user else "#E2E2E8"
        border = "none" if is_user else "1px solid rgba(255, 255, 255, 0.08)"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                color: {text_color};
                border: {border};
                border-radius: 16px;
                border-bottom-right-radius: {'4px' if is_user else '16px'};
                border-bottom-left-radius: {'16px' if is_user else '4px'};
            }}
        """)
        self.setMaximumWidth(600)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 14)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("background: transparent; border: none; font-size: 15px; line-height: 1.4;")
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(label)
        self.setLayout(layout)

class ChatPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("pageSurface")

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)

        # Header
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("AI Coach")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Context-aware productivity assistant")
        subtitle.setObjectName("mutedLabel")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        
        # Context summary widget in header
        context_card = QFrame()
        context_card.setStyleSheet("background: rgba(126, 231, 198, 0.1); border: 1px solid rgba(126, 231, 198, 0.3); border-radius: 8px;")
        ctx_layout = QHBoxLayout(context_card)
        ctx_layout.setContentsMargins(12, 6, 12, 6)
        ctx_layout.addWidget(QLabel("🟢 Analyzing live context"))
        header.addWidget(context_card, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(header)

        # Chat Area
        chat_wrapper = create_card_frame()
        cw_layout = QVBoxLayout(chat_wrapper)
        cw_layout.setContentsMargins(16, 16, 16, 16)
        cw_layout.setSpacing(16)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setSpacing(16)
        self.chat_layout.setContentsMargins(8, 8, 8, 8)
        self.chat_layout.addStretch()
        self.container.setLayout(self.chat_layout)

        self.scroll_area.setWidget(self.container)
        cw_layout.addWidget(self.scroll_area)
        
        # Suggested Prompts
        prompts_layout = QHBoxLayout()
        prompts_layout.setSpacing(12)
        for p in ["Summarize my day", "Why am I losing focus?", "Recommend a break"]:
            btn = QPushButton(p)
            btn.setStyleSheet("background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 6px 12px;")
            btn.clicked.connect(lambda checked, text=p: self.send_prompt(text))
            prompts_layout.addWidget(btn)
        prompts_layout.addStretch()
        cw_layout.addLayout(prompts_layout)
        
        # Input Area
        input_container = QFrame()
        input_container.setStyleSheet("background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px;")
        input_row = QHBoxLayout(input_container)
        input_row.setContentsMargins(8, 8, 8, 8)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask your AI coach about your productivity habits...")
        self.input.setStyleSheet("background: transparent; border: none; font-size: 15px; padding: 8px;")
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setMinimumHeight(36)
        
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.send_btn)
        cw_layout.addWidget(input_container)
        
        layout.addWidget(chat_wrapper, 1)
        main_layout.addWidget(inner)

        self.send_btn.clicked.connect(self.on_send)
        self.input.returnPressed.connect(self.on_send)

        # Initial contextual message
        QTimer.singleShot(500, self.show_initial_greeting)

    def on_show(self):
        fade_in(self)
        
    def show_initial_greeting(self):
        try:
            history = get_chat_history(limit=20)
            if history:
                for entry in history:
                    u = entry.get("user")
                    a = entry.get("ai")
                    if u:
                        self.add_message(u, True)
                    if a:
                        self.add_message(a, False)
                return
        except Exception as e:
            print(f"[ChatPage] History load error: {e}")

        greeting = "Hi! I'm monitoring your context. I notice you've been working steadily. Do you want me to analyze your fatigue trend or suggest a focus strategy?"
        self.add_message(greeting, False)

    def send_prompt(self, text):
        self.input.setText(text)
        self.on_send()

    def add_message(self, text: str, is_user: bool):
        bubble = ChatBubble(text, is_user)
        row = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(4, 2, 4, 2)
        if is_user:
            row_layout.addStretch()
            row_layout.addWidget(bubble)
        else:
            row_layout.addWidget(bubble)
            row_layout.addStretch()
        row.setLayout(row_layout)
        
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)
        fade_in(row, duration=220)
        QTimer.singleShot(50, lambda: animate_scroll_to_bottom(self.scroll_area))

    def set_busy(self, busy: bool):
        self.input.setDisabled(busy)
        self.send_btn.setDisabled(busy)

    def on_send(self):
        prompt = self.input.text().strip()
        if not prompt: return

        self._active_prompt = prompt
        self.add_message(prompt, True)
        self.input.clear()
        self.set_busy(True)
        
        self._typing_bubble = ChatBubble("Analyzing context...", False)
        self._typing_row = QWidget()
        typing_layout = QHBoxLayout()
        typing_layout.setContentsMargins(4, 2, 4, 2)
        typing_layout.addWidget(self._typing_bubble)
        typing_layout.addStretch()
        self._typing_row.setLayout(typing_layout)
        
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self._typing_row)
        fade_in(self._typing_row, duration=180)
        QTimer.singleShot(50, lambda: animate_scroll_to_bottom(self.scroll_area))

        self.chat_thread = QThread()
        self.worker = ChatWorker(prompt)
        self.worker.moveToThread(self.chat_thread)

        self.worker.reply_ready.connect(self.chat_thread.quit)
        self.worker.error.connect(self.chat_thread.quit)
        self.chat_thread.finished.connect(self.chat_thread.deleteLater)
        
        self.chat_thread.started.connect(self.worker.run)
        self.worker.reply_ready.connect(self.on_reply)
        self.worker.error.connect(self.on_error)

        self.chat_thread.start()

    def _remove_typing_bubble(self):
        if hasattr(self, "_typing_row") and self._typing_row:
            self._typing_row.setParent(None)
            self._typing_row = None
        if hasattr(self, "_typing_bubble") and self._typing_bubble:
            self._typing_bubble = None

    def on_reply(self, text):
        self._remove_typing_bubble()
        self.add_message(text, False)
        self.set_busy(False)
        try:
            if hasattr(self, "_active_prompt") and self._active_prompt:
                save_chat_message(self._active_prompt, text)
        except Exception as e:
            print(f"[ChatPage] Save error: {e}")

    def on_error(self, err: str):
        self._remove_typing_bubble()
        self.add_message(err, False)
        self.set_busy(False)
