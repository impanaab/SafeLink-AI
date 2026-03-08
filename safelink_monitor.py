"""
SafeLink AI - Complete System
Shoulder Surfing Detection with Browser Integration

This program:
1. Runs a Flask server listening for activation signals from browser extension
2. Starts webcam monitoring when a login page is detected
3. Detects faces using OpenCV Haar Cascade
4. Alerts user if multiple people (potential shoulder surfers) are detected

Author: SafeLink AI Team
Event: Hackathon 2026
"""

import cv2
import threading
import time
from typing import Optional
from flask import Flask, request, jsonify

# ============================================================================
# CONFIGURATION
# ============================================================================

FLASK_PORT = 5001
WINDOW_TITLE = "SafeLink AI – Shoulder Surfing Monitor"
FPS_TARGET = 30

# Detection thresholds
FACE_DETECTION_SCALE = 1.1
FACE_DETECTION_NEIGHBORS = 5
MIN_FACE_SIZE = (30, 30)

# Color definitions (BGR format for OpenCV)
COLOR_SAFE = (0, 255, 0)        # Green
COLOR_THREAT = (0, 0, 255)      # Red
COLOR_INFO = (255, 255, 255)    # White

# ============================================================================
# GLOBAL STATE
# ============================================================================

_camera_lock = threading.Lock()
_camera_active = False
_camera_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()

# Pre-load cascade classifier for efficiency
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

@app.route('/activate', methods=['POST'])
def activate_protection():
    """
    Endpoint triggered by browser extension when password field is detected.
    Starts camera monitoring in background thread.
    """
    print("[SafeLink AI] Login page detected. Activating camera monitoring.")
    
    try:
        data = request.get_json() if request.is_json else {}
        url = data.get('url', 'unknown')
        print(f"[SafeLink AI] Detected on: {url}")
    except:
        pass
    
    # Start camera monitor in background
    start_camera_monitor()
    
    return jsonify({
        "status": "success",
        "message": "Camera monitoring activated",
        "timestamp": time.time()
    }), 200

@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint."""
    with _camera_lock:
        is_active = _camera_active
    
    return jsonify({
        "status": "running",
        "camera_active": is_active,
        "timestamp": time.time()
    }), 200

# ============================================================================
# CAMERA MONITORING
# ============================================================================

def detect_faces(frame):
    """
    Detect faces in the frame using Haar Cascade.
    
    Args:
        frame: Input frame from webcam
        
    Returns:
        list: Coordinates of detected faces [(x, y, w, h), ...]
    """
    # Convert to grayscale for detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply histogram equalization for better detection in varying light
    gray = cv2.equalizeHist(gray)
    
    # Detect faces
    faces = _face_cascade.detectMultiScale(
        gray,
        scaleFactor=FACE_DETECTION_SCALE,
        minNeighbors=FACE_DETECTION_NEIGHBORS,
        minSize=MIN_FACE_SIZE,
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    return faces

def draw_alerts(frame, faces):
    """
    Draw visual alerts on the frame.
    
    - Green boxes and "SAFE" message if 1 or fewer faces
    - Red boxes and "SHOULDER SURFING DETECTED" if 2+ faces
    
    Args:
        frame: Input frame to draw on
        faces: List of detected face coordinates
        
    Returns:
        frame: Annotated frame
    """
    threat_detected = len(faces) > 1
    box_color = COLOR_THREAT if threat_detected else COLOR_SAFE
    
    # Draw bounding boxes around detected faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
        
        # Label each face
        label_text = "Face"
        label_size, _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(
            frame,
            (x, y - label_size[1] - 8),
            (x + label_size[0], y),
            box_color,
            -1
        )
        cv2.putText(
            frame,
            label_text,
            (x, y - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            COLOR_INFO,
            2
        )
    
    # Draw status banner at top of frame
    banner_height = 90
    overlay = frame.copy()
    
    if threat_detected:
        # Red threat banner
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], banner_height), COLOR_THREAT, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Threat alert text
        alert_text = "⚠ SHOULDER SURFING DETECTED"
        cv2.putText(
            frame,
            alert_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            COLOR_INFO,
            2,
            cv2.LINE_AA
        )
    else:
        # Green safe banner
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], banner_height), COLOR_SAFE, -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Safe status text
        safe_text = "SAFE – No Threat Detected"
        cv2.putText(
            frame,
            safe_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            COLOR_INFO,
            2,
            cv2.LINE_AA
        )
    
    # Display face count
    count_text = f"Faces: {len(faces)}"
    cv2.putText(
        frame,
        count_text,
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        COLOR_INFO,
        2,
        cv2.LINE_AA
    )
    
    # Display instruction at bottom
    instruction_text = "Press 'Q' to stop monitoring"
    cv2.putText(
        frame,
        instruction_text,
        (10, frame.shape[0] - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        COLOR_INFO,
        1,
        cv2.LINE_AA
    )
    
    return frame

def _camera_worker():
    """
    Camera monitoring loop.
    
    Continuously captures frames, detects faces, and displays alerts.
    Runs in background thread until user presses Q or program exits.
    """
    global _camera_active
    
    print("[SafeLink AI] Camera monitoring started")
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[SafeLink AI] ERROR: Cannot access webcam")
        with _camera_lock:
            _camera_active = False
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, FPS_TARGET)
    
    print("[SafeLink AI] Camera initialized successfully")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while not _stop_event.is_set():
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                print("[SafeLink AI] Warning: Failed to read frame from camera")
                continue
            
            frame_count += 1
            
            # Detect faces
            faces = detect_faces(frame)
            
            # Draw visual alerts
            frame = draw_alerts(frame, faces)
            
            # Calculate and display FPS
            elapsed = time.time() - start_time
            if elapsed > 0:
                fps = frame_count / elapsed
                fps_text = f"FPS: {fps:.1f}"
                cv2.putText(
                    frame,
                    fps_text,
                    (frame.shape[1] - 150, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    COLOR_INFO,
                    1,
                    cv2.LINE_AA
                )
            
            # Display frame
            cv2.imshow(WINDOW_TITLE, frame)
            
            # Check for exit key
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("[SafeLink AI] User requested exit (Q key pressed)")
                _stop_event.set()
                break
    
    except Exception as e:
        print(f"[SafeLink AI] ERROR in camera worker: {e}")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        with _camera_lock:
            _camera_active = False
        
        print("[SafeLink AI] Camera monitoring stopped")

def start_camera_monitor():
    """Start camera monitoring in a background thread."""
    global _camera_active, _camera_thread
    
    with _camera_lock:
        if _camera_active:
            print("[SafeLink AI] Camera already monitoring")
            return
        
        _camera_active = True
    
    # Create and start camera thread
    _camera_thread = threading.Thread(target=_camera_worker, daemon=True)
    _camera_thread.start()

# ============================================================================
# MAIN SERVER
# ============================================================================

def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("          SafeLink AI - Shoulder Surfing Protection System")
    print("                    Hackathon 2026 Edition")
    print("="*70)
    print("\nSystem Overview:")
    print("• Browser Extension: Detects login pages")
    print("• Python Backend: Manages camera activation")
    print("• Computer Vision: Real-time face detection")
    print("• Protection: Alerts on shoulder surfing risk")
    print("\n" + "="*70)
    print("\nServer Status:")
    print(f"  Flask Server: http://127.0.0.1:{FLASK_PORT}")
    print(f"  Activation Endpoint: POST /activate")
    print(f"  Status Endpoint: GET /status")
    print("\nInstructions:")
    print("  1. Open Chrome extensions: chrome://extensions/")
    print("  2. Load the SafeLink AI extension folder")
    print("  3. Navigate to a login page (GitHub, Google, etc.)")
    print("  4. When password field appears, camera window will open")
    print("  5. Press 'Q' in camera window to stop monitoring")
    print("\n" + "="*70 + "\n")
    
    # Verify cascade loaded
    if _face_cascade.empty():
        print("[SafeLink AI] ERROR: Failed to load Haar Cascade classifier")
        return 1
    
    print("[SafeLink AI] Background protection active")
    print("[SafeLink AI] Listening for browser activation signals...")
    
    try:
        # Start Flask server (blocking call)
        app.run(
            host='127.0.0.1',
            port=FLASK_PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n[SafeLink AI] Server shutdown requested")
    except Exception as e:
        print(f"[SafeLink AI] ERROR: {e}")
        return 1
    finally:
        _stop_event.set()
        if _camera_thread:
            _camera_thread.join(timeout=2)
        print("[SafeLink AI] SafeLink AI shutdown complete")
    
    return 0

if __name__ == "__main__":
    exit(main())
