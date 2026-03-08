"""
safelink_fast_monitor.py

SafeLink AI fast shoulder surfing monitor.
Performance notes:
- Frames are resized to 50% before detection.
- Face/person detection runs every 3 frames (not every frame).
- Detection uses grayscale images for speed.
"""

import threading
import time

import cv2
import numpy as np
from plyer import notification

OWNER_FACE_PATH = "owner_face.jpg"
WINDOW_TITLE = "SafeLink AI Monitor"
OWNER_MATCH_THRESHOLD = 1800.0
ALERT_COOLDOWN_SECONDS = 8.0


class SafeLinkFastMonitor:
    """Fast and smooth shoulder surfing detector with background monitoring."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        self.owner_face = None
        self.running = False
        self.monitor_thread = None

        self.show_window = False
        self.last_alert_time = 0.0

        self.state_lock = threading.Lock()
        self.latest_draw = {
            "boxes": [],
            "status": "SAFE - Only Owner Detected",
            "threat": False,
            "face_count": 0,
            "people_count": 0,
        }

    def load_owner_face(self):
        """Load owner face template in grayscale and normalize to 100x100."""
        owner_img = cv2.imread(OWNER_FACE_PATH, cv2.IMREAD_GRAYSCALE)
        if owner_img is None or owner_img.size == 0:
            print("[SafeLink AI] ERROR: owner_face.jpg not found. Run register_owner.py first.")
            return False

        self.owner_face = cv2.resize(owner_img, (100, 100), interpolation=cv2.INTER_AREA)
        return True

    def mse_score(self, face_gray):
        """Compute mean squared difference between detected face and owner template."""
        test_face = cv2.resize(face_gray, (100, 100), interpolation=cv2.INTER_AREA)
        diff = test_face.astype(np.float32) - self.owner_face.astype(np.float32)
        return float(np.mean(diff * diff))

    def notify_alert(self):
        """Send desktop notification with cooldown to avoid spam."""
        now = time.time()
        if now - self.last_alert_time < ALERT_COOLDOWN_SECONDS:
            return

        notification.notify(
            title="⚠ SafeLink AI Alert",
            message="Someone is looking at your screen.",
            app_name="SafeLink AI",
            timeout=8,
        )
        self.last_alert_time = now

    def detect_people_fast(self, frame_small):
        """Detect people on half-size frame, then return count and boxes in small-frame coords."""
        people, _weights = self.hog.detectMultiScale(
            frame_small,
            winStride=(4, 4),
            padding=(8, 8),
            scale=1.05,
        )
        return people

    def background_monitor(self):
        """Background thread that continuously captures webcam and updates threat state."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[SafeLink AI] ERROR: Unable to access webcam")
            self.running = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        frame_index = 0
        last_faces_small = []
        last_people_small = []
        last_labels = []

        while self.running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            # PERFORMANCE 1: Process half-size frame for faster detection.
            frame_small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            gray_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

            # PERFORMANCE 2: Run detectors every 3 frames to reduce CPU load.
            if frame_index % 3 == 0:
                faces_small = self.face_cascade.detectMultiScale(
                    gray_small,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(25, 25),
                )

                people_small = self.detect_people_fast(frame_small)

                labels = []
                unknown_found = False
                owner_found = False

                for (x, y, w, h) in faces_small:
                    roi = gray_small[y : y + h, x : x + w]
                    score = self.mse_score(roi)
                    if score <= OWNER_MATCH_THRESHOLD:
                        labels.append("OWNER")
                        owner_found = True
                    else:
                        labels.append("UNKNOWN")
                        unknown_found = True

                face_count = len(faces_small)
                people_count = len(people_small)

                # Detection rules:
                # SAFE: exactly 1 face and owner.
                # THREAT: unknown face OR more than one person.
                threat = unknown_found or people_count > 1
                if not threat and face_count == 1 and owner_found:
                    status = "SAFE - Only Owner Detected"
                elif threat:
                    status = "⚠ SHOULDER SURFING DETECTED"
                else:
                    status = "SAFE - Monitoring"

                if threat:
                    print("[SafeLink AI] Possible shoulder surfing detected")
                    self.notify_alert()
                    self.show_window = True

                last_faces_small = faces_small
                last_people_small = people_small
                last_labels = labels

                with self.state_lock:
                    self.latest_draw = {
                        "boxes": (last_faces_small, last_people_small, last_labels),
                        "status": status,
                        "threat": threat,
                        "face_count": face_count,
                        "people_count": people_count,
                        "frame": frame.copy(),
                    }

            frame_index += 1

            if self.show_window:
                with self.state_lock:
                    draw_state = dict(self.latest_draw)

                draw_frame = draw_state.get("frame", frame).copy()
                faces_small, people_small, labels = draw_state["boxes"]
                status = draw_state["status"]
                threat = draw_state["threat"]

                # Scale small-frame boxes back to full frame.
                for i, (x, y, w, h) in enumerate(faces_small):
                    fx, fy, fw, fh = int(x * 2), int(y * 2), int(w * 2), int(h * 2)
                    label = labels[i] if i < len(labels) else "UNKNOWN"
                    if label == "OWNER":
                        color = (0, 255, 0)
                        tag = "Owner"
                    else:
                        color = (0, 0, 255)
                        tag = "Intruder"

                    cv2.rectangle(draw_frame, (fx, fy), (fx + fw, fy + fh), color, 2)
                    cv2.putText(
                        draw_frame,
                        tag,
                        (fx, max(20, fy - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        color,
                        2,
                        cv2.LINE_AA,
                    )

                # Optional people boxes (from HOG) for behind-user detection context.
                for (x, y, w, h) in people_small:
                    px, py, pw, ph = int(x * 2), int(y * 2), int(w * 2), int(h * 2)
                    cv2.rectangle(draw_frame, (px, py), (px + pw, py + ph), (255, 140, 0), 2)

                # Header status bar.
                bar_color = (0, 0, 255) if threat else (0, 140, 0)
                cv2.rectangle(draw_frame, (0, 0), (draw_frame.shape[1], 90), bar_color, -1)
                cv2.putText(
                    draw_frame,
                    status,
                    (14, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.95,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    draw_frame,
                    f"Faces: {draw_state['face_count']}  People: {draw_state['people_count']}",
                    (14, 74),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.68,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

                cv2.imshow(WINDOW_TITLE, draw_frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q")):
                    self.show_window = False
                    cv2.destroyWindow(WINDOW_TITLE)

            # Tiny sleep keeps UI responsive and avoids tight-loop CPU spikes.
            time.sleep(0.005)

        cap.release()
        cv2.destroyAllWindows()

    def start(self):
        """Start fast monitor in background thread."""
        if self.face_cascade.empty():
            print("[SafeLink AI] ERROR: Failed to load Haar Cascade")
            return

        if not self.load_owner_face():
            return

        print("[SafeLink AI] Fast monitoring active")

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
    monitor = SafeLinkFastMonitor()
    monitor.start()


if __name__ == "__main__":
    main()
