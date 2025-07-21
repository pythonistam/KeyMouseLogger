import sys
import time
import threading
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import QTimer, Qt

# === Логирование ===
log_file = "input_log.txt"
recording_enabled = False
pressed_keys = {}
pressed_buttons = {}
current_keys = set()
lock = threading.Lock()

HOTKEY_COMBINATION = {Key.ctrl_l, Key.shift, KeyCode(char='r')}

def write_log(message):
    if not recording_enabled and not message.startswith("[TOGGLE]"):
        return
    with lock:
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(message + "\n")

def toggle_recording():
    global recording_enabled
    recording_enabled = not recording_enabled
    write_log(f"[TOGGLE] Logging is now {'ENABLED' if recording_enabled else 'DISABLED'}")

# === GUI ===
class RecorderWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Input Recorder")
        self.setFixedSize(250, 150)

        self.label = QLabel("⏸ Запись ВЫКЛ", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 18px;")

        self.btn_toggle = QPushButton("Вкл/Выкл")
        self.btn_toggle.clicked.connect(self.manual_toggle)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.btn_toggle)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(200)

    def manual_toggle(self):
        toggle_recording()

    def update_status(self):
        self.label.setText("▶ Запись ВКЛ" if recording_enabled else "⏸ Запись ВЫКЛ")
        self.label.setStyleSheet("color: green; font-size: 18px;" if recording_enabled else "color: red; font-size: 18px;")

# === Обработчики клавиатуры ===
def on_key_press(key):
    global recording_enabled
    current_keys.add(key)

    if HOTKEY_COMBINATION.issubset(current_keys):
        toggle_recording()
        return

    if not recording_enabled:
        return

    now = time.time()
    key_str = str(key)
    if key_str not in pressed_keys:
        pressed_keys[key_str] = now
        write_log(f"[KEY_DOWN] {key_str} at {now:.6f}")

def on_key_release(key):
    current_keys.discard(key)

    if not recording_enabled:
        return

    now = time.time()
    key_str = str(key)
    start = pressed_keys.pop(key_str, None)
    if start:
        duration = now - start
        write_log(f"[KEY_UP]   {key_str} at {now:.6f} (held {duration:.3f} s)")

# === Мышь ===
def on_click(x, y, button, pressed):
    if not recording_enabled:
        return
    now = time.time()
    b = str(button)
    if pressed:
        pressed_buttons[b] = now
        write_log(f"[MOUSE_DOWN] {b} at ({x},{y}) at {now:.6f}")
    else:
        start = pressed_buttons.pop(b, None)
        if start:
            d = now - start
            write_log(f"[MOUSE_UP]   {b} at ({x},{y}) at {now:.6f} (held {d:.3f} s)")

def on_scroll(x, y, dx, dy):
    if not recording_enabled:
        return
    now = time.time()
    write_log(f"[MOUSE_SCROLL] dx={dx}, dy={dy} at ({x},{y}) at {now:.6f}")

# === Потоки ===
def start_listeners():
    threading.Thread(target=lambda: keyboard.Listener(on_press=on_key_press, on_release=on_key_release).run(), daemon=True).start()
    threading.Thread(target=lambda: mouse.Listener(on_click=on_click, on_scroll=on_scroll).run(), daemon=True).start()

# === Запуск ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = RecorderWindow()
    win.show()
    start_listeners()
    sys.exit(app.exec())
