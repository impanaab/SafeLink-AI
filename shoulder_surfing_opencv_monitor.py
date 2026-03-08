"""
shoulder_surfing_opencv_monitor.py

SafeLink AI - OpenCV-only shoulder surfing monitor.
Uses Haar Cascade + simple owner matching (MSE).
"""

import threading
import time

import cv2
import numpy as np
from plyer import notification

OWNER_FACE_PATH = "owner_face.jpg"
WINDOW_TITLE = "SafeLink AI Monitor"
DETECTION_INTERVAL_SECONDS = 1.2
ALERT_COOLDOWN_SECONDS = 10
OWNER_MATCH_THRESHOLD = 1800.0


class SafeLinkAIMonitor:
    """Shoulder surfing monitor using owner face matching and Haar detection."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.owner_face = None  # Grayscale owner template (100x100)

        self.camera = None
        self.running = False
        self.monitor_thread = None

        self.latest_frame = None
        self.frame_lock = threading.Lock()

        self.last_result = {
            "faces": [],
            "labels": [],
            "status": "SAFE - Only Owner Detected",
            "alert": False,
        }
        self.result_lock = threading.Lock()

        self.last_alert_time = 0.0

    def load_owner_face(self):
        """Load owner_face.jpg in grayscale and normalize to 100x100."""
        print("[SafeLink AI] Loading owner face...")

        owner_gray = cv2.imread(OWNER_FACE_PATH, cv2.IMREAD_GRAYSCALE)
        if owner_gray is None:
            print("[SafeLink AI] ERROR: owner_face.jpg not found. Run register_owner.py first.")
            return False

        if owner_gray.size == 0:
            print("[SafeLink AI] ERROR: owner_face.jpg is empty or invalid")
            return False

        self.owner_face = cv2.resize(owner_gray, (100, 100), interpolation=cv2.INTER_AREA)
        return True

    def initialize_camera(self):
        """Open webcam capture."""
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("[SafeLink AI] ERROR: Unable to access webcam")
            return False

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        return True

    def mean_squared_difference(self, detected_face_gray):
        """Compute MSE between owner face and detected face."""
        resized_detected = cv2.resize(detected_face_gray, (100, 100), interpolation=cv2.INTER_AREA)
        diff = resized_detected.astype(np.float32) - self.owner_face.astype(np.float32)
        return float(np.mean(diff * diff))

    def analyze_frame(self, frame):
        """Detect faces and classify each as OWNER or UNKNOWN PERSON."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(35, 35),
        )

        labels = []
        owner_count = 0
        unknown_present = False

        for (x, y, w, h) in faces:
            face_roi = gray[y : y + h, x : x + w]
            mse = self.mean_squared_difference(face_roi)

            if mse <= OWNER_MATCH_THRESHOLD:
                labels.append("OWNER")
                owner_count += 1
            else:
                labels.append("UNKNOWN PERSON")
                unknown_present = True

        # Detection logic requested:
        # SAFE only when exactly one face and it matches owner.
        if len(faces) == 1 and owner_count == 1:
            status = "SAFE - Only Owner Detected"
            alert = False
        elif len(faces) > 1 or unknown_present:
            status = "⚠ SHOULDER SURFING DETECTED"
            alert = True
        else:
            # No face currently visible; keep clear non-alert status.
            status = "SAFE - Waiting for face"
            alert = False

        return faces, labels, status, alert

    def notify_alert(self):
        """Send desktop alert with cooldown to avoid spam."""
        now = time.time()
        if now - self.last_alert_time < ALERT_COOLDOWN_SECONDS:
            return

        notification.notify(
            title="⚠ SafeLink AI Alert",
            message="Another person detected near your screen.",
            app_name="SafeLink AI",
            timeout=8,
        )
        self.last_alert_time = now

    def background_monitor_loop(self):
        """Analyze latest frame every 1-2 seconds in a background thread."""
        next_check_time = 0.0

        while self.running:
            now = time.time()
            if now < next_check_time:
                time.sleep(0.02)
                continue

            with self.frame_lock:
                frame = None if self.latest_frame is None else self.latest_frame.copy()

            if frame is None:
                time.sleep(0.05)
                continue

            faces, labels, status, alert = self.analyze_frame(frame)

            with self.result_lock:
                self.last_result = {
                    "faces": faces,
                    "labels": labels,
                    "status": status,
                    "alert": alert,
                }

            print(f"[SafeLink AI] Faces detected: {len(faces)}")
            if len(faces) == 1 and labels == ["OWNER"]:
                print("[SafeLink AI] Owner verified")
                print("[SafeLink AI] SAFE")
            elif alert:
                print("[SafeLink AI] Possible shoulder surfing detected")
                self.notify_alert()

            next_check_time = now + DETECTION_INTERVAL_SECONDS

    def draw_visual_output(self, frame, result):
        """Draw colored boxes and status text in monitor window."""
        faces = result["faces"]
        labels = result["labels"]
        status = result["status"]
        alert = result["alert"]

        for (face_box, label) in zip(faces, labels):
            x, y, w, h = face_box
            if label == "OWNER":
                color = (0, 255, 0)
                tag = "Owner"
            else:
                color = (0, 0, 255)
                tag = "Unknown person"

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame,
                tag,
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2,
                cv2.LINE_AA,
            )

        banner_color = (0, 0, 255) if alert else (0, 130, 0)
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 85), banner_color, -1)
        cv2.putText(
            frame,
            status,
            (15, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.95,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Faces detected: {len(faces)}",
            (15, 72),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Press Q to exit",
            (15, frame.shape[0] - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    def run(self):
        """Start system, launch background thread, and show monitor window."""
        if self.face_cascade.empty():
            print("[SafeLink AI] ERROR: Failed to load Haar Cascade")
            return

        print("[SafeLink AI] System started")
        print("[SafeLink AI] Background monitoring active")

        if not self.load_owner_face():
            return

        print("[SafeLink AI] Waiting for activity...")

        if not self.initialize_camera():
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self.background_monitor_loop, daemon=True)
        self.monitor_thread.start()

        while self.running:
            ok, frame = self.camera.read()
            if not ok:
                time.sleep(0.02)
                continue

            with self.frame_lock:
                self.latest_frame = frame.copy()

            with self.result_lock:
                result = {
                    "faces": list(self.last_result["faces"]),
                    "labels": list(self.last_result["labels"]),
                    "status": self.last_result["status"],
                    "alert": self.last_result["alert"],
                }

            self.draw_visual_output(frame, result)
            cv2.imshow(WINDOW_TITLE, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q")):
                self.running = False
                break

        self.cleanup()

    def cleanup(self):
        """Release camera and close windows."""
        self.running = False
        if self.monitor_thread is not None:
            self.monitor_thread.join(timeout=1.5)
        if self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()


def main():
    monitor = SafeLinkAIMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
