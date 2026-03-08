"""SafeLink AI sensitive monitor.

Runs in the background and opens the webcam only when typing behavior looks
like password entry (more than 6 characters quickly, without spaces).
"""

import threading
import time

import cv2
from pynput import keyboard


class SafeLinkSensitiveMonitor:
    """Background monitor for sensitive typing + shoulder-surfing detection."""

    def __init__(self) -> None:
        self.running = True
        self.lock = threading.Lock()

        # Typing pattern state used for password-like behavior detection.
        self.current_token = ""
        self.token_start_time = 0.0
        self.last_key_time = 0.0
        self.quick_pause_reset_seconds = 1.8
        self.min_sensitive_length = 7  # "more than 6"
        self.max_sensitive_duration = 2.8

        # Camera/monitor state.
        self.monitor_active = False
        self.last_trigger_time = 0.0
        self.trigger_cooldown_seconds = 4.0

        # Performance tuning.
        self.detect_every_n_frames = 3
        self.frame_scale = 0.5

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.listener = keyboard.Listener(on_press=self._on_key_press)

    def start(self) -> None:
        """Start background listener and keep process alive."""
        print("[SafeLink AI] Background monitoring active")
        print("[SafeLink AI] Waiting for sensitive action...")
        self.listener.start()

        try:
            while self.running:
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.running = False
        finally:
            self.stop()

    def stop(self) -> None:
        """Gracefully stop background listener and any OpenCV windows."""
        self.running = False
        try:
            self.listener.stop()
        except Exception:
            pass
        cv2.destroyAllWindows()

    def _reset_token(self) -> None:
        """Reset current token and timing state."""
        self.current_token = ""
        self.token_start_time = 0.0

    def _on_key_press(self, key: keyboard.KeyCode) -> None:
        """Observe keystrokes and trigger webcam monitor for sensitive typing."""
        if not self.running:
            return

        now = time.time()
        if now - self.last_key_time > self.quick_pause_reset_seconds:
            self._reset_token()
        self.last_key_time = now

        # Any spacing key breaks password-like token.
        if key in (keyboard.Key.space, keyboard.Key.enter, keyboard.Key.tab):
            self._reset_token()
            return

        # Keep backspace behavior realistic.
        if key == keyboard.Key.backspace:
            self.current_token = self.current_token[:-1]
            return

        char = getattr(key, "char", None)
        if not char or not char.isprintable():
            return

        if not self.current_token:
            self.token_start_time = now

        self.current_token = (self.current_token + char)[-64:]

        if self._is_sensitive_typing(now):
            print("[SafeLink AI] Sensitive typing detected")
            self._start_monitor_thread()
            self._reset_token()

    def _is_sensitive_typing(self, now: float) -> bool:
        """Return True for quick, continuous tokens with no spaces."""
        if len(self.current_token) < self.min_sensitive_length:
            return False

        # Token has no spaces because space resets token, but keep explicit guard.
        if " " in self.current_token:
            return False

        duration = now - self.token_start_time
        return duration <= self.max_sensitive_duration

    def _start_monitor_thread(self) -> None:
        """Start webcam monitoring if not already active and not in cooldown."""
        with self.lock:
            now = time.time()
            if self.monitor_active:
                return
            if now - self.last_trigger_time < self.trigger_cooldown_seconds:
                return

            self.monitor_active = True
            self.last_trigger_time = now

        threading.Thread(target=self._run_webcam_monitor, daemon=True).start()

    def _run_webcam_monitor(self) -> None:
        """Open webcam and detect shoulder surfing using face count."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[SafeLink AI] Could not open webcam")
            with self.lock:
                self.monitor_active = False
            return

        frame_index = 0
        face_boxes = []
        face_count = 0

        while self.running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.02)
                continue

            frame_index += 1

            # Resize frame for speed.
            frame_small = cv2.resize(frame, (0, 0), fx=self.frame_scale, fy=self.frame_scale)

            # Detect faces every few frames to reduce CPU load.
            if frame_index % self.detect_every_n_frames == 0:
                gray_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
                faces_small = self.face_cascade.detectMultiScale(
                    gray_small,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(40, 40),
                )

                scale_back = int(1 / self.frame_scale)
                face_boxes = [
                    (x * scale_back, y * scale_back, w * scale_back, h * scale_back)
                    for (x, y, w, h) in faces_small
                ]
                face_count = len(face_boxes)

            threat = face_count > 1
            status_text = "⚠ SHOULDER SURFING DETECTED" if threat else "SAFE"
            status_color = (0, 0, 255) if threat else (0, 255, 0)

            # Draw face boxes: green for safe, red for intruder scenario.
            for (x, y, w, h) in face_boxes:
                box_color = (0, 0, 255) if threat else (0, 255, 0)
                cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)

            # Show status text on monitor window.
            if threat:
                detail = "⚠ SHOULDER SURFING DETECTED"
            else:
                detail = "SAFE - Only Owner Detected"

            cv2.putText(
                frame,
                status_text,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                status_color,
                2,
            )
            cv2.putText(
                frame,
                detail,
                (20, 68),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                status_color,
                2,
            )
            cv2.putText(
                frame,
                "Press Q to close monitor",
                (20, 98),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (220, 220, 220),
                1,
            )

            cv2.imshow("SafeLink AI Monitor", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyWindow("SafeLink AI Monitor")

        with self.lock:
            self.monitor_active = False

        print("[SafeLink AI] Waiting for sensitive action...")


if __name__ == "__main__":
    monitor = SafeLinkSensitiveMonitor()
    monitor.start()
