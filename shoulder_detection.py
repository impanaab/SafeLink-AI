"""
Shoulder Surfing Detection Module for SafeLink AI
=================================================

This module uses webcam-based face detection to identify potential
shoulder surfing attacks by detecting multiple people near the screen.

Shoulder Surfing Attack Explanation:
------------------------------------
Shoulder surfing is a visual hacking technique where an attacker
observes the victim's screen, keyboard, or other input devices to
obtain sensitive information like passwords, PINs, or confidential data.

Detection Strategy:
-------------------
1. Activate webcam and capture video frames
2. Use OpenCV's Haar Cascade classifier for face detection
3. Count the number of faces detected in each frame
4. If more than 1 face is detected consistently, raise an alert

This helps protect users working on sensitive information in public spaces.
"""

import cv2
import os

def detect_shoulder_surfer():
    """
    Detects potential shoulder surfing by counting faces via webcam.
    
    The function captures ~50 frames from the webcam and uses face detection
    to identify if multiple people are present near the screen.
    
    Returns:
        dict: A dictionary containing:
            - status: "risk" or "safe"
            - message: Descriptive message about detection results
    """
    
    print("[Shoulder Detection] Initializing webcam...")
    
    # STEP 1: Initialize webcam
    # cv2.VideoCapture(0) opens the default webcam
    cap = cv2.VideoCapture(0)
    
    # Check if webcam is accessible
    if not cap.isOpened():
        print("[Shoulder Detection] ⚠️ ERROR: Cannot access webcam")
        return {
            "status": "error",
            "message": "⚠️ Cannot access webcam. Please check camera permissions."
        }
    
    # STEP 2: Load Haar Cascade face detection model
    # This is a pre-trained model that comes with OpenCV
    # It detects frontal faces in images
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    # Verify the cascade loaded successfully
    if face_cascade.empty():
        print("[Shoulder Detection] ⚠️ ERROR: Could not load face detection model")
        cap.release()
        return {
            "status": "error",
            "message": "⚠️ Face detection model failed to load."
        }
    
    print("[Shoulder Detection] Starting face detection (analyzing 50 frames)...")
    
    # STEP 3: Capture and analyze frames
    frames_to_analyze = 50  # Number of frames to check
    suspicious_frame_count = 0  # Count frames with multiple faces
    total_frames_processed = 0
    
    for i in range(frames_to_analyze):
        # Capture a single frame from the webcam
        ret, frame = cap.read()
        
        # Check if frame was captured successfully
        if not ret:
            print(f"[Shoulder Detection] Warning: Could not read frame {i+1}")
            continue
        
        total_frames_processed += 1
        
        # STEP 4: Convert frame to grayscale
        # Haar Cascade works better with grayscale images
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # STEP 5: Detect faces in the frame
        # Parameters explained:
        # - scaleFactor: compensates for faces closer/farther from camera
        # - minNeighbors: higher value = fewer false positives, but might miss faces
        # - minSize: minimum face size to detect (in pixels)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # STEP 6: Count detected faces
        face_count = len(faces)
        
        # If more than 1 face detected, it's suspicious
        if face_count > 1:
            suspicious_frame_count += 1
            print(f"[Shoulder Detection] Frame {i+1}: {face_count} faces detected ⚠️")
        elif face_count == 1:
            print(f"[Shoulder Detection] Frame {i+1}: {face_count} face detected ✓")
        else:
            print(f"[Shoulder Detection] Frame {i+1}: No faces detected")
    
    # STEP 7: Release the webcam
    cap.release()
    print(f"[Shoulder Detection] Webcam released. Analysis complete.")
    
    # STEP 8: Determine risk level
    # If more than 20% of frames show multiple faces, raise alert
    threshold = 0.2 * frames_to_analyze
    
    print(f"[Shoulder Detection] Suspicious frames: {suspicious_frame_count}/{total_frames_processed}")
    
    if suspicious_frame_count > threshold:
        return {
            "status": "risk",
            "message": f"⚠️ Shoulder Surfing Risk Detected! Multiple people detected in {suspicious_frame_count} frames. Someone may be watching your screen."
        }
    else:
        return {
            "status": "safe",
            "message": f"✓ No shoulder surfing detected. You appear to be working alone. ({total_frames_processed} frames analyzed)"
        }


# Test the module independently
if __name__ == "__main__":
    print("=" * 60)
    print("SafeLink AI - Shoulder Surfing Detection Module Test")
    print("=" * 60)
    print("This will activate your webcam for a few seconds...")
    print("=" * 60)
    result = detect_shoulder_surfer()
    print("\nResult:")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
