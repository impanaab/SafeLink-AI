"""
owner_register.py

SafeLink AI owner registration script.
Captures one face image from webcam and saves it as owner_face.jpg.
"""

import cv2


def register_owner_face(output_path="owner_face.jpg"):
    """Open webcam and save owner face image when user presses S."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[SafeLink AI] ERROR: Unable to access webcam")
        return

    window_title = "Register Owner Face"
    print("Look at the camera and press S to capture your face.")

    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        display = frame.copy()
        cv2.putText(
            display,
            "Look at the camera and press S to capture your face.",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            display,
            "Press Q to quit without saving.",
            (15, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.imshow(window_title, display)
        key = cv2.waitKey(1) & 0xFF

        if key in (ord("s"), ord("S")):
            cv2.imwrite(output_path, frame)
            print("[SafeLink AI] Owner face registered successfully")
            break

        if key in (ord("q"), ord("Q")):
            print("[SafeLink AI] Registration cancelled")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    register_owner_face()
