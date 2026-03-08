"""SafeLink AI background shoulder-surfing monitor.

Continuously analyzes webcam frames in the background and alerts when an
unknown face is detected.
"""

import threading
import time

import cv2
from plyer import notification


class SafeLinkBackgroundMonitor:
    """Background monitor using Haar face detection + LBPH owner matching."""

    def __init__(self) -> None:
        self.running = True
        self.lock = threading.Lock()

        # Run detection on every frame for immediate response.
        self.detect_every_n_frames = 1
        self.frame_index = 0
        self.owner_confidence_threshold = 60.0
        self.owner_margin_threshold = 8.0
        self.notification_cooldown = 4
        self.last_notification_time = 0.0
        self.frame_scale = 0.5
        self.face_scale_factor = 1.08
        self.face_min_neighbors = 4
        self.face_min_size = (28, 28)
        # Side peeping is considered near left/right edges (outside middle 40%).
        self.side_left_boundary_ratio = 0.30
        self.side_right_boundary_ratio = 0.70

        self.monitor_visible = False
        self.latest_frame = None

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        try:
            self.recognizer.read("owner_model.yml")
        except Exception:
            raise RuntimeError(
                "owner_model.yml not found. Run register_owner.py first."
            )

        # Use a low-latency backend on Windows when available.
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            raise RuntimeError("Unable to access webcam")

        # Lower camera latency and CPU load.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def send_alert(self) -> None:
        """Send desktop alert with cooldown to avoid repeated notifications."""
        now = time.time()
        if now - self.last_notification_time < self.notification_cooldown:
            return

        try:
            notification.notify(
                title="⚠ SafeLink AI Alert",
                message="Intruder detected looking at your screen",
                app_name="SafeLink AI",
                timeout=5,
            )
        except Exception:
            pass

        self.last_notification_time = now

    def analyze_frame(self, frame):
        """Detect faces and classify exactly one owner, others as intruders."""
        frame_small = cv2.resize(frame, (0, 0), fx=self.frame_scale, fy=self.frame_scale)
        gray_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
        gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces_small = self.face_cascade.detectMultiScale(
            gray_small,
            scaleFactor=self.face_scale_factor,
            minNeighbors=self.face_min_neighbors,
            minSize=self.face_min_size,
        )

        detections = []
        candidates = []

        scale_back = int(round(1 / self.frame_scale))
        for (x_s, y_s, w_s, h_s) in faces_small:
            x = int(x_s * scale_back)
            y = int(y_s * scale_back)
            w = int(w_s * scale_back)
            h = int(h_s * scale_back)

            face_roi = gray_full[y : y + h, x : x + w]
            if face_roi.size == 0:
                continue

            face_input = cv2.resize(face_roi, (200, 200))
            _, confidence = self.recognizer.predict(face_input)

            candidates.append((x, y, w, h, float(confidence)))

        owner_index = -1
        if candidates:
            # Pick only one strongest candidate as owner if it is clearly reliable.
            sorted_idx = sorted(range(len(candidates)), key=lambda i: candidates[i][4])
            best_idx = sorted_idx[0]
            best_conf = candidates[best_idx][4]
            second_conf = candidates[sorted_idx[1]][4] if len(candidates) > 1 else 999.0

            if (
                best_conf < self.owner_confidence_threshold
                and (second_conf - best_conf) >= self.owner_margin_threshold
            ):
                owner_index = best_idx

        intruder_found = False
        side_peeping_found = False
        frame_width = frame.shape[1]
        side_left_boundary = frame_width * self.side_left_boundary_ratio
        side_right_boundary = frame_width * self.side_right_boundary_ratio

        for idx, (x, y, w, h, confidence) in enumerate(candidates):
            if idx == owner_index:
                label = "OWNER"
                color = (0, 255, 0)
            else:
                label = "INTRUDER"
                color = (0, 0, 255)
                intruder_found = True

                # Highlight likely side peeping when intruder appears near edges.
                center_x = x + (w / 2.0)
                if center_x < side_left_boundary or center_x > side_right_boundary:
                    label = "SIDE PEEPING"
                    color = (0, 255, 255)
                    side_peeping_found = True

            detections.append((x, y, w, h, label, color, confidence))

        return detections, intruder_found, side_peeping_found

    def background_loop(self) -> None:
        """Continuously process webcam frames and trigger alerts on threats."""
        cached_detections = []
        cached_unknown = False
        cached_side_peeping = False

        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            self.frame_index += 1

            # Skip frames for smoother CPU usage.
            if self.frame_index % self.detect_every_n_frames == 0:
                cached_detections, cached_unknown, cached_side_peeping = self.analyze_frame(frame)

            display = frame.copy()
            for (x, y, w, h, label, color, confidence) in cached_detections:
                cv2.rectangle(display, (x, y), (x + w, y + h), color, 2)
                cv2.putText(
                    display,
                    f"{label} ({confidence:.0f})",
                    (x, max(20, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )

            status_text = "SAFE"
            status_color = (0, 255, 0)
            if cached_unknown or cached_side_peeping:
                status_text = "⚠ SHOULDER SURFING DETECTED"
                status_color = (0, 0, 255)

                with self.lock:
                    self.monitor_visible = True

                self.send_alert()

            cv2.putText(
                display,
                status_text,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                status_color,
                2,
            )
            cv2.putText(
                display,
                "Press Q to stop",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (220, 220, 220),
                1,
            )

            with self.lock:
                self.latest_frame = display

        self.cap.release()

    def run(self) -> None:
        """Start background worker and show monitor window only on threat."""
        print("[SafeLink AI] Background monitoring started")

        worker = threading.Thread(target=self.background_loop, daemon=True)
        worker.start()

        while self.running:
            with self.lock:
                show_monitor = self.monitor_visible
                frame = None if self.latest_frame is None else self.latest_frame.copy()

            if show_monitor and frame is not None:
                cv2.imshow("SafeLink AI Monitor", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                    self.running = False
                    break
            else:
                time.sleep(0.01)

        self.running = False
        worker.join(timeout=1.0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    monitor = SafeLinkBackgroundMonitor()
    monitor.run()
