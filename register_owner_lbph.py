"""SafeLink AI owner registration using LBPH face recognition."""

import cv2
import numpy as np


def register_owner() -> None:
    """Capture owner face samples and train/save the LBPH model."""
    print("[SafeLink AI] Starting owner registration...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam")
        return

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    max_samples = 30
    collected_faces = []
    frame_count = 0

    while len(collected_faces) < max_samples:
        ok, frame = cap.read()
        if not ok:
            continue

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100),
        )

        if len(faces) > 0:
            # Use the largest detected face for more stable owner samples.
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Capture one sample every 2 frames to reduce duplicates.
            if frame_count % 2 == 0:
                face_roi = gray[y : y + h, x : x + w]
                face_resized = cv2.resize(face_roi, (200, 200))
                collected_faces.append(face_resized)

        cv2.putText(
            frame,
            "Look at the camera. Capturing face samples...",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            f"Samples: {len(collected_faces)}/{max_samples}",
            (10, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Register Owner Face", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(collected_faces) < 10:
        print(f"[ERROR] Not enough samples captured: {len(collected_faces)}")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    labels = np.zeros(len(collected_faces), dtype=np.int32)
    recognizer.train(collected_faces, labels)
    recognizer.save("owner_model.yml")

    print("[SafeLink AI] Owner model trained successfully")


if __name__ == "__main__":
    register_owner()
