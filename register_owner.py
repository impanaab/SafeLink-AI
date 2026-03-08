"""SafeLink AI owner registration with OpenCV LBPH recognizer."""

import cv2
import numpy as np


def main() -> None:
    """Capture owner face samples and train LBPH owner model."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[SafeLink AI] ERROR: Unable to access webcam")
        return

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    if face_cascade.empty():
        print("[SafeLink AI] ERROR: Failed to load Haar Cascade")
        cap.release()
        return

    max_samples = 40
    frame_index = 0
    samples = []

    while len(samples) < max_samples:
        ok, frame = cap.read()
        if not ok:
            continue

        frame_index += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(90, 90),
        )

        if len(faces) > 0:
            # Take the largest detected face for stable owner samples.
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Sample every other frame to reduce near-duplicate images.
            if frame_index % 2 == 0:
                face = gray[y : y + h, x : x + w]
                face = cv2.resize(face, (200, 200))
                samples.append(face)

        cv2.putText(
            frame,
            f"Capturing owner samples: {len(samples)}/{max_samples}",
            (12, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Press Q to cancel",
            (12, 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow("Register Owner Face", frame)

        if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(samples) < 10:
        print("[SafeLink AI] ERROR: Not enough samples to train model")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    labels = np.zeros(len(samples), dtype=np.int32)
    recognizer.train(samples, labels)
    recognizer.save("owner_model.yml")

    print("[SafeLink AI] Owner model trained successfully")


if __name__ == "__main__":
    main()
