"""SafeLink AI Flask server.

Receives browser-extension trigger events and starts webcam monitoring for
shoulder-surfing detection using OpenCV Haar + LBPH recognition.
"""

import threading
import time

import cv2
from flask import Flask, jsonify, request
from werkzeug.serving import make_server


app = Flask(__name__)

# Load Haar cascade for face detection.
FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Load LBPH owner model once at server startup.
RECOGNIZER = cv2.face.LBPHFaceRecognizer_create()
MODEL_LOADED = False
try:
    RECOGNIZER.read("owner_model.yml")
    MODEL_LOADED = True
except Exception:
    MODEL_LOADED = False

MONITOR_LOCK = threading.Lock()
MONITOR_RUNNING = False
MONITOR_PAUSED_BY_USER = False
SERVER_LOCK = threading.Lock()
HTTP_SERVER = None


def _shutdown_server() -> None:
    """Stop the Flask server so the running command exits cleanly."""
    global HTTP_SERVER

    with SERVER_LOCK:
        server = HTTP_SERVER

    if server is not None:
        try:
            server.shutdown()
            print("[SafeLink AI] Server stopped after monitor closed")
        except Exception:
            pass


def _run_monitor() -> None:
    """Open webcam and perform real-time owner/threat classification."""
    global MONITOR_RUNNING, MONITOR_PAUSED_BY_USER

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[SafeLink AI] Could not open webcam")
        with MONITOR_LOCK:
            MONITOR_RUNNING = False
        return

    frame_index = 0
    detect_every_n_frames = 3
    cached_faces = []
    stopped_by_q = False

    while True:
        with MONITOR_LOCK:
            if not MONITOR_RUNNING:
                break

        ok, frame = cap.read()
        if not ok:
            time.sleep(0.02)
            continue

        frame_index += 1

        # Resize for speed as requested.
        frame_small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

        if frame_index % detect_every_n_frames == 0:
            gray_small = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
            gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces_small = FACE_CASCADE.detectMultiScale(
                gray_small,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(40, 40),
            )

            cached_faces = []
            for (x_s, y_s, w_s, h_s) in faces_small:
                # Scale coordinates back to full-size frame.
                x = int(x_s * 2)
                y = int(y_s * 2)
                w = int(w_s * 2)
                h = int(h_s * 2)

                face_roi = gray_full[y : y + h, x : x + w]
                if face_roi.size == 0:
                    continue

                face_resized = cv2.resize(face_roi, (200, 200))

                # Owner recognition using LBPH confidence threshold.
                if MODEL_LOADED:
                    _, confidence = RECOGNIZER.predict(face_resized)
                    if confidence < 70:
                        label = "OWNER"
                        color = (0, 255, 0)
                    else:
                        label = "UNKNOWN - THREAT"
                        color = (0, 0, 255)
                else:
                    label = "UNKNOWN - THREAT"
                    color = (0, 0, 255)

                cached_faces.append((x, y, w, h, label, color))

        # Draw boxes and labels.
        for (x, y, w, h, label, color) in cached_faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame,
                label,
                (x, max(y - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        cv2.imshow("SafeLink AI Monitor", frame)

        # Stop if user closes the monitor window directly.
        if cv2.getWindowProperty("SafeLink AI Monitor", cv2.WND_PROP_VISIBLE) < 1:
            with MONITOR_LOCK:
                MONITOR_RUNNING = False
            break

        # Press Q to close webcam monitor.
        if cv2.waitKey(1) & 0xFF == ord("q"):
            with MONITOR_LOCK:
                MONITOR_RUNNING = False
                MONITOR_PAUSED_BY_USER = True
            stopped_by_q = True
            break

    cap.release()
    cv2.destroyWindow("SafeLink AI Monitor")

    with MONITOR_LOCK:
        MONITOR_RUNNING = False

    if stopped_by_q:
        print("[SafeLink AI] Monitor stopped by user. Background trigger paused.")
        print("[SafeLink AI] Call POST /resume (or restart server) to enable triggers again.")

    # Requested behavior: end running command when monitor is closed.
    _shutdown_server()


@app.after_request
def add_cors_headers(response):
    """Allow extension requests from browser pages/content scripts."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/start", methods=["POST", "OPTIONS"])
def start_monitor():
    """Start webcam monitoring when extension detects a password field."""
    global MONITOR_RUNNING, MONITOR_PAUSED_BY_USER

    if request.method == "OPTIONS":
        return ("", 204)

    with MONITOR_LOCK:
        if MONITOR_PAUSED_BY_USER:
            return (
                jsonify(
                    {
                        "status": "stopped_by_user",
                        "message": "Monitor paused after Q. Call POST /resume to enable again.",
                    }
                ),
                200,
            )

        if MONITOR_RUNNING:
            return jsonify({"status": "already_running"}), 200

        MONITOR_RUNNING = True

    threading.Thread(target=_run_monitor, daemon=True).start()
    return jsonify({"status": "started"}), 200


@app.route("/resume", methods=["POST", "OPTIONS"])
def resume_monitor():
    """Resume extension-triggered monitoring after user paused with Q."""
    global MONITOR_PAUSED_BY_USER

    if request.method == "OPTIONS":
        return ("", 204)

    with MONITOR_LOCK:
        MONITOR_PAUSED_BY_USER = False

    return jsonify({"status": "resumed"}), 200


if __name__ == "__main__":
    print("SafeLink AI Server running")
    HTTP_SERVER = make_server("127.0.0.1", 5000, app)
    HTTP_SERVER.serve_forever()
