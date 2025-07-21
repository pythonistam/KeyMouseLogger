import time
import re
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key

keyboard = KeyboardController()
mouse = MouseController()

log_file = "input_log.txt"

# === Распознавание строки клавиши (обычная, спецклавиша, ascii код) ===
def parse_key(key_str):
    if key_str.startswith("Key."):
        try:
            return getattr(Key, key_str.split('.')[1])
        except AttributeError:
            return None
    elif key_str.startswith("<") and key_str.endswith(">"):
        try:
            return chr(int(key_str[1:-1]))  # <97> => 'a'
        except:
            return None
    elif len(key_str) == 1:
        return key_str
    return None

# === Распознавание строки события ===
def parse_log_line(line):
    # [KEY_DOWN] 'a' at 123.456
    m1 = re.match(r"\[KEY_DOWN\] '(.+?)' at ([\d.]+)", line)
    m2 = re.match(r"\[KEY_UP\]   '(.+?)' at ([\d.]+)", line)
    m3 = re.match(r"\[KEY_DOWN\] (Key\.\w+|<\d+>) at ([\d.]+)", line)
    m4 = re.match(r"\[KEY_UP\]   (Key\.\w+|<\d+>) at ([\d.]+)", line)
    m_mouse_down = re.match(r"\[MOUSE_DOWN\] (Button\.\w+) at \((\-?\d+), (\-?\d+)\) at ([\d.]+)", line)
    m_mouse_up = re.match(r"\[MOUSE_UP\]   (Button\.\w+) at \((\-?\d+), (\-?\d+)\) at ([\d.]+)", line)
    m_scroll = re.match(r"\[MOUSE_SCROLL\] dx=(\-?\d+), dy=(\-?\d+) at \((\-?\d+), (\-?\d+)\) at ([\d.]+)", line)

    if m1:
        return ("key_down", m1.group(1), float(m1.group(2)))
    if m2:
        return ("key_up", m2.group(1), float(m2.group(2)))
    if m3:
        return ("key_down", m3.group(1), float(m3.group(2)))
    if m4:
        return ("key_up", m4.group(1), float(m4.group(2)))
    if m_mouse_down:
        return ("mouse_down", m_mouse_down.group(1), int(m_mouse_down.group(2)), int(m_mouse_down.group(3)), float(m_mouse_down.group(4)))
    if m_mouse_up:
        return ("mouse_up", m_mouse_up.group(1), int(m_mouse_up.group(2)), int(m_mouse_up.group(3)), float(m_mouse_up.group(4)))
    if m_scroll:
        return ("scroll", int(m_scroll.group(1)), int(m_scroll.group(2)),
                int(m_scroll.group(3)), int(m_scroll.group(4)), float(m_scroll.group(5)))
    return None

# === Воспроизведение лога ===
def replay_log(file_path):
    time.sleep(5)  # Небольшая задержка перед началом воспроизведения
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    events = []
    for line in lines:
        parsed = parse_log_line(line)
        if parsed:
            events.append(parsed)

    if not events:
        print("❌ Лог пуст или формат не распознан.")
        return

    print(f"🔁 Начало воспроизведения {len(events)} событий...\n")
    start_time = events[0][-1]

    for i, event in enumerate(events):
        e_type = event[0]
        delay = event[-1] - start_time if i == 0 else event[-1] - events[i - 1][-1]
        time.sleep(delay)

        if e_type == "key_down":
            key = parse_key(event[1])
            if key is not None:
                keyboard.press(key)
                print(f"[КЛАВИША ВНИЗ] {repr(key)}")
            else:
                print(f"[ОШИБКА] key_down: {event[1]}")
        elif e_type == "key_up":
            key = parse_key(event[1])
            if key is not None:
                keyboard.release(key)
                print(f"[КЛАВИША ВВЕРХ] {repr(key)}")
            else:
                print(f"[ОШИБКА] key_up: {event[1]}")
        elif e_type == "mouse_down":
            btn = getattr(Button, event[1].split(".")[1])
            x, y = event[2], event[3]
            mouse.position = (x, y)
            mouse.press(btn)
            print(f"[МЫШЬ ВНИЗ] {btn} на ({x},{y})")
        elif e_type == "mouse_up":
            btn = getattr(Button, event[1].split(".")[1])
            x, y = event[2], event[3]
            mouse.position = (x, y)
            mouse.release(btn)
            print(f"[МЫШЬ ВВЕРХ] {btn} на ({x},{y})")
        elif e_type == "scroll":
            dx, dy, x, y = event[1], event[2], event[3], event[4]
            mouse.position = (x, y)
            mouse.scroll(dx, dy)
            print(f"[ПРОКРУТКА] dx={dx}, dy={dy} в ({x},{y})")

    print("\n✅ Воспроизведение завершено.")

if __name__ == "__main__":
    print("⏳ Воспроизведение действий из input_log.txt...")
    replay_log(log_file)
