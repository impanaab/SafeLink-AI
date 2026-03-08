# SafeLink AI - Shoulder Surfing Monitor

## Real-Time Shoulder Surfing Detection System

A comprehensive computer vision solution for detecting shoulder surfing attacks using dual detection methods: face detection (Haar Cascade) and person detection (HOG Descriptor).

---

## Features

✅ **Real-time webcam monitoring**  
✅ **Dual detection system** (faces + full-body person detection)  
✅ **Visual alerts** with color-coded bounding boxes  
✅ **Live threat analysis** with on-screen status display  
✅ **Optimized performance** for real-time processing  
✅ **Screenshot capability** for documentation  

---

## How It Works

### Detection Strategy

1. **Face Detection** - Uses OpenCV Haar Cascade to detect faces in real-time
2. **Person Detection** - Uses HOG (Histogram of Oriented Gradients) descriptor to detect human bodies
3. **Threat Analysis** - Combines both detections to identify shoulder surfing scenarios

### Threat Logic

| Scenario | Detection | Visual Feedback | Status |
|----------|-----------|----------------|--------|
| Only user present | 1 face/person | 🟢 Green boxes | **SAFE** |
| Someone watching | 2+ faces/people | 🔴 Red boxes | **⚠ SHOULDER SURFING DETECTED** |

---

## Installation

### Prerequisites

```bash
# Install required libraries
pip install opencv-python numpy
```

Or install from requirements.txt:

```bash
cd SafeLinkAI
pip install -r requirements.txt
```

### Camera Permissions

Ensure your laptop webcam is:
- Connected and functional
- Not being used by another application
- Permissions granted for Python/your IDE to access the camera

---

## Usage

### Running the Monitor

```bash
cd SafeLinkAI
python shoulder_surfing_monitor.py
```

### Controls

- **Q** - Quit the monitor
- **S** - Save screenshot (saved as `safelink_screenshot_N.jpg`)

### Expected Behavior

When you run the script:

1. Camera initializes and detection models load
2. Real-time video window opens: **"SafeLink AI - Shoulder Surfing Monitor"**
3. System continuously monitors for threats
4. Visual feedback shows:
   - **Green** boxes around detected people when safe
   - **Red** boxes and **⚠ WARNING** banner when multiple people detected
   - Detection count (faces/people) in the banner
   - FPS counter for performance monitoring

---

## Demo Scenarios

### Scenario 1: Safe - Working Alone
```
Status: ✅ SAFE - No Threat Detected
Display: Green bounding box around your face/body
Banner: Green with "SAFE - No Threat Detected"
```

### Scenario 2: Threat - Someone Behind You
```
Status: ⚠ WARNING: SHOULDER SURFING DETECTED!
Display: Red bounding boxes around all detected people
Banner: Red with threat warning and detection count
```

### Scenario 3: High Risk - Multiple People
```
Status: ⚠ WARNING: SHOULDER SURFING DETECTED!
Display: Multiple red boxes
Banner: Shows exact count of faces and people detected
```

---

## Code Structure

The system is organized into clean, modular functions:

```python
class ShoulderSurfingMonitor:
    
    initialize_camera()      # Start webcam
    load_detection_models()  # Load Haar Cascade + HOG
    
    detect_faces()           # Face detection using Haar Cascade
    detect_people()          # Person detection using HOG
    
    analyze_threat()         # Threat assessment logic
    draw_alerts()            # Visual feedback rendering
    
    process_frame()          # Main processing pipeline
    run()                    # Continuous monitoring loop
```

---

## Performance Optimization

The system includes several optimizations for real-time performance:

1. **Frame skipping** - HOG detection runs every 2nd frame (configurable)
2. **Downscaling** - HOG processes at 0.5x resolution for speed
3. **Histogram equalization** - Improves face detection in varying lighting
4. **Efficient rendering** - Minimal overhead display code

Typical performance: **20-30 FPS** on modern laptops

---

## Integration with SafeLink AI Flask App

The main SafeLink AI web dashboard uses a simplified version in `shoulder_detection.py` that:
- Runs headless (no display window)
- Analyzes 50 frames quickly
- Returns JSON status for the web interface

This `shoulder_surfing_monitor.py` is the **full demo/testing version** with:
- Live video window
- Visual alerts
- Continuous operation
- Perfect for hackathon demonstrations

---

## Troubleshooting

### Camera Not Opening

```
[Camera] ERROR: Cannot access webcam!
```

**Solutions:**
- Close other applications using the camera (Zoom, Teams, etc.)
- Check camera privacy settings (Windows Settings → Privacy → Camera)
- Try running as administrator
- Verify camera with: `cv2.VideoCapture(0).isOpened()`

### Low Performance / Lag

**Solutions:**
- Increase `frame_skip` value (line 27: `self.frame_skip = 3` or higher)
- Reduce camera resolution (lines 65-66)
- Disable person detection (comment out `detect_people()` calls)
- Close background applications

### No Faces Detected

**Solutions:**
- Ensure good lighting
- Face the camera directly
- Adjust `scaleFactor` and `minNeighbors` in `detect_faces()`
- Check if Haar Cascade loaded correctly

---

## Technical Details

### Detection Models

**Haar Cascade (Face Detection)**
- Pre-trained model: `haarcascade_frontalface_default.xml`
- Included with OpenCV
- Fast, efficient for frontal faces
- Works best with direct lighting

**HOG Descriptor (Person Detection)**
- OpenCV default people detector
- Detects full human silhouettes
- More robust than face detection alone
- Slightly slower, hence frame skipping

### Libraries Used

```python
import cv2      # OpenCV for computer vision
import numpy    # Numerical operations
import threading # For future async capabilities
import time     # Timing and delays
```

---

## Hackathon Demo Tips

1. **Setup**: Test camera before presentation
2. **Lighting**: Ensure good room lighting for best detection
3. **Positioning**: Position camera to see your workspace
4. **Demo Flow**:
   - Start monitor → Show **SAFE** status
   - Have teammate approach from behind → Show **THREAT** detection
   - Explain dual detection (faces + bodies)
   - Save screenshot showing threat detection

---

## Future Enhancements

Potential improvements for production version:
- [ ] Alert sound when threat detected
- [ ] Save threat event logs with timestamps
- [ ] Multi-camera support
- [ ] Deep learning models (YOLO, SSD) for better accuracy
- [ ] Mobile app integration
- [ ] Cloud alerting system

---

## License & Credits

**Project:** SafeLink AI  
**Event:** Hackathon 2026  
**Technology:** OpenCV, Python, Computer Vision  

Built for protecting sensitive information in public workspaces.

---

## Contact & Support

For issues or questions about this shoulder surfing monitor:
1. Check camera permissions
2. Verify OpenCV installation: `python -c "import cv2; print(cv2.__version__)"`
3. Review console output for detailed error messages

---

**Happy Hacking! Stay Safe with SafeLink AI! 🔒**
