"""
shoulder_surfing_monitor.py

SafeLink AI background shoulder surfing monitor using OpenCV only.
Allowed external libraries: opencv-python, numpy, plyer.
"""

import threading
import time

import cv2
import numpy as np
from plyer import notification

OWNER_FACE_PATH = "owner_face.jpg"
WINDOW_TITLE = "SafeLink AI Monitor"
DETECTION_INTERVAL_SECONDS = 1.2  # Run heavy detection every 1-2 seconds.
ALERT_COOLDOWN_SECONDS = 10
OWNER_MATCH_THRESHOLD = 1800.0


class SafeLinkMonitor:
    """Background monitor that detects possible shoulder surfing events."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.owner_face_gray = None
        self.camera = None

        self.monitoring = False
        self.monitor_thread = None
        self.last_alert_time = 0.0

        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.analysis_lock = threading.Lock()
        self.last_analysis = {
            "faces": [],
            "labels": [],
            "status": "SAFE - Only Owner Detected",
            "is_alert": False,
        }

    def load_owner_face(self):
        """Load owner_face.jpg and create a normalized owner face template."""
        owner_image = cv2.imread(OWNER_FACE_PATH)
        if owner_image is None:
            print("[SafeLink AI] ERROR: owner_face.jpg not found. Run owner_register.py first.")
            return False

        owner_gray = cv2.cvtColor(owner_image, cv2.COLOR_BGR2GRAY)
        owner_faces = self.face_cascade.detectMultiScale(
            owner_gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40),
        )

        if len(owner_faces) == 0:
            print("[SafeLink AI] ERROR: No face detected in owner_face.jpg")
            return False

        # Use the largest detected face from owner image.
        x, y, w, h = max(owner_faces, key=lambda box: box[2] * box[3])
        owner_roi = owner_gray[y : y + h, x : x + w]
        self.owner_face_gray = cv2.resize(owner_roi, (100, 100), interpolation=cv2.INTER_AREA)
        return True

    def initialize_camera(self):
        """Initialize webcam using OpenCV."""
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            print("[SafeLink AI] ERROR: Unable to access webcam")
            return False

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        return True

    def face_difference_score(self, face_gray):
        """Compare detected face with owner face using mean squared difference."""
        if self.owner_face_gray is None:
            return float("inf")

        resized_face = cv2.resize(face_gray, (100, 100), interpolation=cv2.INTER_AREA)
        diff = resized_face.astype(np.float32) - self.owner_face_gray.astype(np.float32)
        return float(np.mean(diff * diff))

    def analyze_frame(self, frame):
        """Detect faces and classify each face as OWNER or UNKNOWN PERSON."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(35, 35),
        )

        labels = []
        owner_matches = 0

        for (x, y, w, h) in faces:
            face_roi = gray[y : y + h, x : x + w]
            mse = self.face_difference_score(face_roi)
            if mse <= OWNER_MATCH_THRESHOLD:
                labels.append("OWNER")
                owner_matches += 1
            else:
                labels.append("UNKNOWN")

        # Requested logic:
        # 1 face and matches owner => SAFE
        # 2+ faces => SHOULDER SURFING DETECTED
        if len(faces) == 1 and owner_matches == 1:
            status = "SAFE - Only Owner Detected"
            is_alert = False
        elif len(faces) >= 2:
            status = "⚠ SHOULDER SURFING DETECTED"
            is_alert = True
        else:
            # Keeps status explicit when user is not clearly recognized.
            status = "ALERT - Unknown person detected"
            is_alert = True

        return faces, labels, status, is_alert

    def show_alert(self):
        """Show desktop notification with cooldown."""
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

    def background_worker(self):
        """Background thread that runs detection every 1-2 seconds."""
        next_detection_time = 0.0

        while self.monitoring:
            now = time.time()
            if now < next_detection_time:
                time.sleep(0.02)
                continue

            with self.frame_lock:
                if self.latest_frame is None:
                    frame_to_analyze = None
                else:
                    frame_to_analyze = self.latest_frame.copy()

            if frame_to_analyze is None:
                time.sleep(0.05)
                continue

            faces, labels, status, is_alert = self.analyze_frame(frame_to_analyze)

            with self.analysis_lock:
                self.last_analysis = {
                    "faces": faces,
                    "labels": labels,
                    "status": status,
                    "is_alert": is_alert,
                }

            print(f"[SafeLink AI] Faces detected: {len(faces)}")
            if is_alert:
                print("[SafeLink AI] Possible shoulder surfing detected")
                self.show_alert()
            else:
                print("[SafeLink AI] SAFE")

            next_detection_time = now + DETECTION_INTERVAL_SECONDS

    def draw_overlay(self, frame, analysis):
        """Draw boxes and large status text for SAFE or ALERT visibility."""
        faces = analysis["faces"]
        labels = analysis["labels"]
        status = analysis["status"]
        is_alert = analysis["is_alert"]

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
                0.7,
                color,
                2,
                cv2.LINE_AA,
            )

        banner_color = (0, 0, 255) if is_alert else (0, 140, 0)
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 85), banner_color, -1)
        cv2.putText(
            frame,
            status,
            (15, 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.95,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            f"Faces detected: {len(faces)}",
            (15, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
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

    def start_background_monitor(self):
        """Start monitor thread and display webcam output."""
        if self.face_cascade.empty():
            print("[SafeLink AI] ERROR: Failed to load Haar cascade")
            return
        if not self.load_owner_face():
            return
        if not self.initialize_camera():
            return

        print("[SafeLink AI] System started")
        print("[SafeLink AI] Background monitoring active")
        print("[SafeLink AI] Waiting for activity...")

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.background_worker, daemon=True)
        self.monitor_thread.start()

        while self.monitoring:
            ok, frame = self.camera.read()
            if not ok:
                time.sleep(0.02)
                continue

            with self.frame_lock:
                self.latest_frame = frame.copy()

            with self.analysis_lock:
                analysis = {
                    "faces": list(self.last_analysis["faces"]),
                    "labels": list(self.last_analysis["labels"]),
                    "status": self.last_analysis["status"],
                    "is_alert": self.last_analysis["is_alert"],
                }

            self.draw_overlay(frame, analysis)
            cv2.imshow(WINDOW_TITLE, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q")):
                self.monitoring = False
                break

        self.cleanup()

    def cleanup(self):
        """Release resources and close windows."""
        self.monitoring = False
        if self.monitor_thread is not None:
            self.monitor_thread.join(timeout=1.5)
        if self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()


def main():
    monitor = SafeLinkMonitor()
    monitor.start_background_monitor()


if __name__ == "__main__":
    main()
