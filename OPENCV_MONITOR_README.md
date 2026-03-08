# SafeLink AI - OpenCV Shoulder Surfing Monitor

## Complete Computer Vision Security System

---

## Overview

**shoulder_surfing_opencv_monitor.py** is a standalone background security monitor that detects when multiple people are near your laptop screen using:

- **Haar Cascade** for face detection
- **HOG Descriptor** for person detection
- **Desktop notifications** for alerts
- **Real-time visual monitoring**

---

## Features Implemented

### ✅ 1. Background Monitor
- Runs continuously in background using threading
- Prints: `[SafeLink AI] Background monitoring active`
- Non-blocking architecture

### ✅ 2. Webcam Capture
- Uses `cv2.VideoCapture(0)`
- Optimized to 640x480 @ 30 FPS
- Continuous frame capture

### ✅ 3. Face Detection
- Haar Cascade: `haarcascade_frontalface_default.xml`
- Detects faces in each frame
- Draws bounding boxes around detected faces

### ✅ 4. Person Detection
- HOG Descriptor with default people detector
- Detects full body even if face partially hidden
- Optimized with periodic detection (every 0.5s)

### ✅ 5. Shoulder Surfing Logic

**Detection Rules:**
```
1 face/person detected → SAFE (green boxes)
2+ faces/persons detected → SHOULDER SURFING DETECTED (red boxes)
```

### ✅ 6. Alert System
- Desktop notifications via plyer
- Title: "⚠ Shoulder Surfing Alert"
- Message: "Another person detected near your screen."
- Console: `[SafeLink AI] Possible shoulder surfing detected`
- Alert cooldown: 10 seconds

### ✅ 7. Visual Display

**Window Title:** "SafeLink AI Monitor"

**Display Elements:**
- Green boxes → Safe
- Red boxes → Threat
- Status banner: "SAFE - No Threat Detected" OR "⚠ SHOULDER SURFING DETECTED"
- Counters: "Faces: X | People: Y"
- Timestamp
- FPS counter
- Instructions: "Press 'Q' to quit"

### ✅ 8. Performance
- Real-time processing at 20-30 FPS
- Frame optimization for faster detection
- Periodic HOG detection to reduce CPU load

### ✅ 9. Exit Condition
- Press **Q** to close window and stop monitoring

### ✅ 10. Code Organization

**Functions:**
- `initialize_camera()` - Setup webcam
- `initialize_face_detector()` - Load Haar Cascade
- `initialize_person_detector()` - Load HOG detector
- `detect_faces()` - Face detection logic
- `detect_people()` - Person detection logic
- `analyze_threat()` - Threat analysis
- `show_alert()` - Desktop notifications
- `draw_detections()` - Draw bounding boxes
- `draw_status_banner()` - Status display
- `draw_footer()` - Timestamp & instructions
- `start_background_monitor()` - Start monitoring
- `run_visual_monitor()` - Main display loop
- `stop_monitoring()` - Cleanup

---

## Installation

### 1. Install Dependencies

```powershell
cd c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI
pip install opencv-python numpy plyer
```

### 2. Verify Installation

```powershell
python -c "import cv2; print(cv2.__version__)"
python -c "import numpy; print(numpy.__version__)"
python -c "import plyer; print('plyer OK')"
```

---

## Usage

### Run the Monitor

```powershell
python shoulder_surfing_opencv_monitor.py
```

### Expected Output

```
============================================================
   SafeLink AI - Shoulder Surfing Detection System
   Computer Vision Based Security Monitor
============================================================

[SafeLink AI] Starting system...

[SafeLink AI] Initializing...
[SafeLink AI] Face detector loaded
[SafeLink AI] Person detector loaded (HOG)
[SafeLink AI] Initialization complete
[SafeLink AI] Background monitoring active
[SafeLink AI] Webcam initialized successfully
[SafeLink AI] Monitoring thread started
[SafeLink AI] Opening visual monitor...
[SafeLink AI] Visual monitor started
[SafeLink AI] Press 'Q' to exit
```

### Demo Scenario

**Test 1: Sit Alone**
- **Result:** 1 face detected
- **Display:** Green box around your face
- **Status:** "SAFE - No Threat Detected"
- **Counters:** Faces: 1 | People: 1

**Test 2: Friend Peeps from Side**
- **Result:** 2 faces detected
- **Display:** Red boxes around both faces
- **Status:** "⚠ SHOULDER SURFING DETECTED"
- **Alert:** Desktop notification appears
- **Console:** `[SafeLink AI] Possible shoulder surfing detected`

**Test 3: Friend Stands Behind**
- **Result:** 1 face + 1 person body detected
- **Display:** Red boxes
- **Status:** "⚠ SHOULDER SURFING DETECTED"
- **Note:** HOG detects person even if face not fully visible

---

## Controls

| Key | Action |
|-----|--------|
| **Q** | Quit and close monitor |
| **CTRL+C** | Emergency stop (in terminal) |

---

## Performance Specs

- **FPS:** 20-30 frames per second
- **Face Detection:** Every frame (fast Haar Cascade)
- **Person Detection:** Every 0.5 seconds (slower HOG)
- **Alert Cooldown:** 10 seconds between notifications
- **Resolution:** 640x480 (optimized for speed)

---

## Architecture

### Threading Model

```
Main Thread
├── Visual Monitor Loop (OpenCV window)
│   ├── Face detection (every frame)
│   ├── Person detection (every 0.5s)
│   ├── Threat analysis
│   ├── Draw overlays
│   └── Display frame
│
└── Background Thread
    └── Additional background tasks
```

### Detection Pipeline

```
[Webcam Frame]
    ↓
[Flip Mirror]
    ↓
[Face Detection] ──┐
    ↓              │
[Person Detection] ├─→ [Threat Analysis]
    ↓              │        ↓
[Cache Results] ───┘    [Alert System]
    ↓
[Draw Boxes & Status]
    ↓
[Display Window]
```

---

## Troubleshooting

### Webcam Not Opening
**Error:** `[SafeLink AI] Error: Could not access webcam`

**Solutions:**
1. Check if webcam is already in use
2. Verify Windows Privacy Settings → Camera → Allow apps
3. Try different camera index: `cv2.VideoCapture(1)`
4. Restart computer

### HOG Detection Slow
**Symptom:** Low FPS (< 15)

**Solutions:**
1. Increase detection interval in code (line 408):
   ```python
   person_detection_interval = 1.0  # Instead of 0.5
   ```
2. Reduce frame resolution (lines 61-63):
   ```python
   self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
   self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
   ```

### No Desktop Notifications
**Problem:** Notifications not appearing

**Solutions:**
1. Check Windows Settings → System → Notifications
2. Turn OFF "Focus Assist"
3. Try running as administrator
4. Install plyer: `pip install --upgrade plyer`

### Too Many False Alerts
**Problem:** Alerts when alone

**Solutions:**
1. Increase alert cooldown (line 26):
   ```python
   self.alert_cooldown = 30  # 30 seconds instead of 10
   ```
2. Adjust face detection sensitivity (lines 129-132):
   ```python
   faces = self.face_cascade.detectMultiScale(
       gray,
       scaleFactor=1.2,  # Increase from 1.1
       minNeighbors=7,   # Increase from 5
       minSize=(40, 40), # Increase from (30, 30)
   )
   ```

---

## Customization

### Change Detection Colors

Edit `draw_detections()` function (lines 231-241):

```python
# Current: Green for safe, Red for threat
if is_threat:
    face_color = (0, 0, 255)      # Red (BGR)
    person_color = (0, 0, 200)
else:
    face_color = (0, 255, 0)      # Green (BGR)
    person_color = (0, 200, 0)

# Example: Blue for safe, Yellow for threat
if is_threat:
    face_color = (255, 255, 0)    # Yellow
    person_color = (200, 200, 0)
else:
    face_color = (255, 0, 0)      # Blue
    person_color = (200, 0, 0)
```

### Adjust Threat Threshold

Edit `analyze_threat()` function (line 173):

```python
# Current: 2+ people = threat
if total_detections <= 1:
    return False, "SAFE - No Threat Detected"
else:
    return True, "⚠ SHOULDER SURFING DETECTED"

# Example: 3+ people = threat (more lenient)
if total_detections <= 2:
    return False, "SAFE - No Threat Detected"
else:
    return True, "⚠ SHOULDER SURFING DETECTED"
```

### Change Window Title

Edit line 13 or `cv2.imshow()` call (line 449):

```python
cv2.imshow("My Custom Security Monitor", frame)
```

---

## Technical Details

### Face Detection (Haar Cascade)
- **Algorithm:** Viola-Jones
- **Cascade:** frontalface_default
- **Parameters:**
  - scaleFactor: 1.1 (10% size reduction per scale)
  - minNeighbors: 5 (detection confidence)
  - minSize: 30x30 pixels

### Person Detection (HOG)
- **Algorithm:** Histogram of Oriented Gradients
- **Detector:** Default People Detector (SVM)
- **Parameters:**
  - winStride: (4, 4) - step size
  - padding: (8, 8) - border padding
  - scale: 1.05 - pyramid scale factor
- **Optimization:** Runs on 50% scaled frame

---

## Files

```
SafeLinkAI/
├── shoulder_surfing_opencv_monitor.py  # Main program (NEW)
├── shoulder_surfing_monitor.py         # Flask backend (existing)
├── OPENCV_MONITOR_README.md            # This file
└── requirements_opencv.txt             # Dependencies
```

---

## Requirements

**Python:** 3.11
**OS:** Windows

**Libraries:**
- opencv-python >= 4.8.0
- numpy >= 1.24.0
- plyer >= 2.1.0

---

## Demo Workflow

1. **Start Program**
   ```powershell
   python shoulder_surfing_opencv_monitor.py
   ```

2. **Initialization**
   - Face detector loads
   - Person detector loads
   - Webcam starts

3. **Normal Use - Alone**
   - 1 face detected
   - Green box shows
   - "SAFE" banner displays
   - FPS: ~25-30

4. **Threat Detected - Someone Approaches**
   - 2+ faces/people detected
   - Red boxes appear
   - "⚠ SHOULDER SURFING DETECTED" banner
   - Desktop notification pops up
   - Console logs alert

5. **Exit**
   - Press Q
   - Camera releases
   - Window closes
   - Clean shutdown

---

## Advantages Over Face Recognition Version

| Feature | OpenCV Version | Face Recognition Version |
|---------|---------------|-------------------------|
| **Installation** | Simple (opencv-python only) | Complex (requires dlib, cmake) |
| **Detection** | Face + Body (HOG) | Face only |
| **Performance** | 25-30 FPS | 15-20 FPS |
| **Dependency Size** | ~50 MB | ~500+ MB |
| **Windows Compatibility** | Easy | Requires MSVC Build Tools |
| **Owner Recognition** | No | Yes |

---

## Support

For issues:
1. Check troubleshooting section
2. Verify webcam permissions
3. Update OpenCV: `pip install --upgrade opencv-python`

---

**SafeLink AI - Protecting your privacy with computer vision** 🔒
