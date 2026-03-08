"""
SafeLink AI - Background Sensitive Typing + Camera Security Monitor

This program runs in standby mode and listens to keyboard input events.
When rapid, continuous typing without spaces is detected, it activates a
real-time webcam monitor for shoulder surfing detection.
"""

import threading
import time
from typing import Optional

import cv2
from pynput import keyboard

# Detection thresholds for sensitive typing
MIN_CONTIGUOUS_CHARS = 7          # More than 6 characters
SHORT_INTERVAL_SECONDS = 2.5      # Must happen quickly
ALERT_COOLDOWN_SECONDS = 4.0      # Prevent repeated trigger spam

WINDOW_TITLE = "SafeLink AI Security Monitor"

# Shared state for typing pattern analysis
_state_lock = threading.Lock()
_sequence_length = 0
_sequence_start_time: Optional[float] = None
_last_key_time: Optional[float] = None
_last_alert_time = 0.0

# Shared state for camera lifecycle
_camera_lock = threading.Lock()
_camera_active = False
_stop_event = threading.Event()

# Load cascade once to avoid repeated initialization overhead.
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def _reset_sequence() -> None:
    """Reset the current typing sequence counters."""
    global _sequence_length, _sequence_start_time, _last_key_time
    _sequence_length = 0
    _sequence_start_time = None
    _last_key_time = None


def detect_faces(frame):
    """
    Detect faces using Haar Cascade and return full-size frame coordinates.

    Uses a downscaled grayscale image for better real-time performance.
    """
    scale = 0.75
    small = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    faces_small = _face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(28, 28),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    if len(faces_small) == 0:
        return []

    inv = 1.0 / scale
    return [
        (int(x * inv), int(y * inv), int(w * inv), int(h * inv))
        for (x, y, w, h) in faces_small
    ]


def draw_alerts(frame, faces):
    """
    Draw face boxes and security status text.

    - Green boxes when <= 1 face
    - Red boxes when > 1 face
    """
    threat = len(faces) > 1
    box_color = (0, 0, 255) if threat else (0, 255, 0)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)

    status_text = "SAFE"
    status_color = (0, 255, 0)

    if threat:
        status_text = "\u26a0 SHOULDER SURFING DETECTED"
        status_color = (0, 0, 255)

    cv2.putText(
        frame,
        status_text,
        (14, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        status_color,
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        f"Faces: {len(faces)} | Press Q to stop",
        (14, 66),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    return frame


def _camera_worker() -> None:
    """Camera loop worker. Runs until user presses Q or program exits."""
    global _camera_active

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Unable to open webcam. Camera monitor not started.")
        with _camera_lock:
            _camera_active = False
        return

    # Balanced resolution for real-time speed + visibility.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while not _stop_event.is_set():
        ok, frame = cap.read()
        if not ok:
            continue

        faces = detect_faces(frame)
        frame = draw_alerts(frame, faces)

        cv2.imshow(WINDOW_TITLE, frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            _stop_event.set()
            break

    cap.release()
    cv2.destroyAllWindows()

    with _camera_lock:
        _camera_active = False


def start_camera_monitor() -> None:
    """Start camera monitor in a background thread if not already running."""
    global _camera_active

    with _camera_lock:
        if _camera_active:
            return
        _camera_active = True

    thread = threading.Thread(target=_camera_worker, daemon=True)
    thread.start()


def activate_monitor() -> None:
    """Trigger shoulder surfing protection when sensitive typing is detected."""
    print("Sensitive input detected. Activating shoulder surfing protection.")
    start_camera_monitor()


def detect_sensitive_typing(char_typed: str, event_time: float) -> bool:
    """
    Analyze typed characters and detect sensitive typing behavior.

    Sensitive typing behavior:
    - continuous typing of more than 6 characters
    - no spaces
    - within a short time interval
    """
    global _sequence_length, _sequence_start_time, _last_key_time, _last_alert_time

    with _state_lock:
        if char_typed.isspace():
            _reset_sequence()
            return False

        if len(char_typed) != 1 or not char_typed.isprintable():
            return False

        if _last_key_time is not None and (event_time - _last_key_time) > SHORT_INTERVAL_SECONDS:
            _reset_sequence()

        if _sequence_start_time is None:
            _sequence_start_time = event_time

        _sequence_length += 1
        _last_key_time = event_time
        elapsed = event_time - _sequence_start_time

        if _sequence_length >= MIN_CONTIGUOUS_CHARS and elapsed <= SHORT_INTERVAL_SECONDS:
            if (event_time - _last_alert_time) >= ALERT_COOLDOWN_SECONDS:
                _last_alert_time = event_time
                _reset_sequence()
                return True

        return False


def _on_key_press(key: keyboard.KeyCode) -> None:
    """Handle keypress events from pynput listener."""
    if _stop_event.is_set():
        return

    event_time = time.time()

    try:
        char_typed = key.char if key.char is not None else ""
    except AttributeError:
        if key in (keyboard.Key.space, keyboard.Key.enter, keyboard.Key.tab):
            char_typed = " "
        else:
            char_typed = ""

    if detect_sensitive_typing(char_typed, event_time):
        activate_monitor()


def start_keyboard_listener() -> keyboard.Listener:
    """Start keyboard listener in the background thread."""
    listener = keyboard.Listener(on_press=_on_key_press)
    listener.start()
    return listener


def _standby_loop() -> None:
    """Keep process alive in standby mode while listener runs in background."""
    print("SafeLink AI standby mode active. Listening for sensitive typing...")
    print("Camera stays off until sensitive input is detected.")

    while not _stop_event.is_set():
        time.sleep(0.25)


def main() -> None:
    """Program entry point."""
    if _face_cascade.empty():
        print("Failed to load Haar Cascade model.")
        return

    listener = start_keyboard_listener()
    standby_thread = threading.Thread(target=_standby_loop, daemon=True)
    standby_thread.start()

    try:
        while not _stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping SafeLink AI monitor...")
        _stop_event.set()
    finally:
        listener.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
