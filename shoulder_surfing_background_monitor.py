"""
shoulder_surfing_background_monitor.py

SafeLink AI background shoulder surfing detector using OpenCV + NumPy.
"""

import threading
import time

import cv2
import numpy as np
from plyer import notification

OWNER_FACE_PATH = "owner_face.jpg"
WINDOW_TITLE = "SafeLink AI Monitor"
OWNER_MATCH_THRESHOLD = 1800.0
DETECTION_INTERVAL_SECONDS = 2.0
ALERT_COOLDOWN_SECONDS = 10.0

# UI colors (BGR)
COLOR_OWNER = (60, 190, 90)
COLOR_UNKNOWN = (70, 80, 230)
COLOR_BG_DARK = (22, 22, 22)
COLOR_TEXT = (245, 245, 245)


class SafeLinkBackgroundMonitor:
    """Background monitor that detects unknown viewers using face similarity."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.owner_face = None

        self.running = False
        self.monitor_thread = None
        self.show_monitor_window = False
        self.last_alert_time = 0.0

    def load_owner_face(self):
        """Load owner face template from disk and normalize to 100x100."""
        owner_gray = cv2.imread(OWNER_FACE_PATH, cv2.IMREAD_GRAYSCALE)
        if owner_gray is None or owner_gray.size == 0:
            print("[SafeLink AI] ERROR: owner_face.jpg not found. Run register_owner.py first.")
            return False

        self.owner_face = cv2.resize(owner_gray, (100, 100), interpolation=cv2.INTER_AREA)
        return True

    def face_difference(self, detected_face):
        """Compute mean squared difference between owner and detected face."""
        resized_detected = cv2.resize(detected_face, (100, 100), interpolation=cv2.INTER_AREA)
        diff = resized_detected.astype(np.float32) - self.owner_face.astype(np.float32)
        return float(np.mean(diff * diff))

    def classify_faces(self, gray_frame, faces):
        """Classify each detected face as OWNER or UNKNOWN PERSON."""
        labels = []
        unknown_present = False

        for (x, y, w, h) in faces:
            roi = gray_frame[y : y + h, x : x + w]
            score = self.face_difference(roi)
            if score <= OWNER_MATCH_THRESHOLD:
                labels.append("OWNER")
            else:
                labels.append("UNKNOWN PERSON")
                unknown_present = True

        return labels, unknown_present

    def evaluate_status(self, face_count, labels, unknown_present):
        """Apply shoulder-surfing detection rules."""
        if face_count == 1 and labels == ["OWNER"]:
            return "SAFE - Only Owner Detected", False

        if face_count > 1 or unknown_present:
            return "SHOULDER SURFING DETECTED", True

        return "SAFE - No face detected", False

    def send_alert(self):
        """Show desktop alert with cooldown control."""
        now = time.time()
        if now - self.last_alert_time < ALERT_COOLDOWN_SECONDS:
            return

        notification.notify(
            title="SafeLink AI Alert",
            message="Another person detected looking at your screen.",
            app_name="SafeLink AI",
            timeout=8,
        )
        self.last_alert_time = now

    def draw_monitor_window(self, frame, faces, labels, status, is_alert):
        """Render clean monitor UI with clear status and labels."""
        h, w = frame.shape[:2]

        # Subtle dark glass panels for readability.
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 112), COLOR_BG_DARK, -1)
        cv2.rectangle(overlay, (0, h - 40), (w, h), COLOR_BG_DARK, -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        # Face boxes + tags.
        for (box, label) in zip(faces, labels):
            x, y, bw, bh = box
            if label == "OWNER":
                color = COLOR_OWNER
                text = "Owner"
            else:
                color = COLOR_UNKNOWN
                text = "Unknown"

            cv2.rectangle(frame, (x, y), (x + bw, y + bh), color, 2)

            tag_w = 94 if text == "Unknown" else 74
            tag_y0 = max(0, y - 28)
            cv2.rectangle(frame, (x, tag_y0), (x + tag_w, tag_y0 + 24), color, -1)
            cv2.putText(
                frame,
                text,
                (x + 8, tag_y0 + 17),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        # Status chip (top-left).
        chip_color = COLOR_UNKNOWN if is_alert else COLOR_OWNER
        chip_text = "ALERT" if is_alert else "SAFE"
        cv2.rectangle(frame, (14, 14), (130, 48), chip_color, -1)
        cv2.putText(
            frame,
            chip_text,
            (34, 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # Main status line.
        cv2.putText(
            frame,
            status,
            (148, 39),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.78,
            COLOR_TEXT,
            2,
            cv2.LINE_AA,
        )

        # Count badge (top-right).
        count_text = f"Faces: {len(faces)}"
        badge_w = 126
        cv2.rectangle(frame, (w - badge_w - 14, 14), (w - 14, 48), (45, 45, 45), -1)
        cv2.putText(
            frame,
            count_text,
            (w - badge_w, 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            COLOR_TEXT,
            2,
            cv2.LINE_AA,
        )

        # Footer information.
        clock_text = time.strftime("%H:%M:%S")
        cv2.putText(
            frame,
            "Press Q to close monitor",
            (14, h - 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.56,
            COLOR_TEXT,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            clock_text,
            (w - 98, h - 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.56,
            COLOR_TEXT,
            1,
            cv2.LINE_AA,
        )

        cv2.imshow(WINDOW_TITLE, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            print("[SafeLink AI] Q pressed. Stopping monitor.")
            self.show_monitor_window = False
            self.running = False
            cv2.destroyWindow(WINDOW_TITLE)

    def background_monitor(self):
        """Background thread: open webcam, capture every 2 seconds, and detect faces."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[SafeLink AI] ERROR: Unable to access webcam")
            self.running = False
            return

        while self.running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(DETECTION_INTERVAL_SECONDS)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(35, 35),
            )

            labels, unknown_present = self.classify_faces(gray, faces)
            status, is_alert = self.evaluate_status(len(faces), labels, unknown_present)

            print(f"[SafeLink AI] Faces detected: {len(faces)}")
            if len(faces) == 1 and labels == ["OWNER"]:
                print("[SafeLink AI] Owner verified")
            if is_alert:
                print("[SafeLink AI] Possible shoulder surfing detected")
                self.send_alert()
                self.show_monitor_window = True

            if self.show_monitor_window and self.running:
                self.draw_monitor_window(frame.copy(), faces, labels, status, is_alert)

            time.sleep(DETECTION_INTERVAL_SECONDS)

        cap.release()
        cv2.destroyAllWindows()

    def start(self):
        """Initialize system and start background monitoring thread."""
        if self.face_cascade.empty():
            print("[SafeLink AI] ERROR: Failed to load Haar Cascade")
            return

        if not self.load_owner_face():
            return

        print("[SafeLink AI] System started")
        print("[SafeLink AI] Background monitoring active")

        self.running = True
        self.monitor_thread = threading.Thread(target=self.background_monitor, daemon=True)
        self.monitor_thread.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False

        if self.monitor_thread is not None:
            self.monitor_thread.join(timeout=2)


def main():
    monitor = SafeLinkBackgroundMonitor()
    monitor.start()


if __name__ == "__main__":
    main()
