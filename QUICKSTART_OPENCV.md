# SafeLink AI - OpenCV Monitor Quick Start

## 30-Second Setup

### Step 1: Install Dependencies
```powershell
cd c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI
pip install opencv-python numpy plyer
```

### Step 2: Run the Monitor
```powershell
python shoulder_surfing_opencv_monitor.py
```

### Step 3: Test the System

**Scenario 1: Sit Alone**
- You'll see a green box around your face
- Status: "SAFE - No Threat Detected"

**Scenario 2: Have Someone Look Over Your Shoulder**
- Red boxes appear around both faces
- Status: "⚠ SHOULDER SURFING DETECTED"
- Desktop notification pops up

**Scenario 3: Someone Stands Behind You**
- Person detection triggers even if face not visible
- Alert appears

---

## What You'll See

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

A window titled "SafeLink AI Monitor" opens showing:
- Live webcam feed
- Green/red bounding boxes
- Status banner at top
- Face and people counters
- FPS display
- Timestamp

---

## Detection Logic

```
1 person detected:
  → Green boxes
  → "SAFE - No Threat Detected"

2+ people detected:
  → Red boxes
  → "⚠ SHOULDER SURFING DETECTED"
  → Desktop notification
  → Console alert
```

---

## How It Works

**Face Detection:**
- Uses OpenCV Haar Cascade
- Detects frontal faces
- Fast (runs every frame)

**Person Detection:**
- Uses HOG Descriptor
- Detects full body
- Slower (runs every 0.5s)

**Combined Logic:**
- Takes max(faces, people)
- If count > 1, triggers alert

---

## Controls

| Key | Action |
|-----|--------|
| Q | Quit monitor |
| CTRL+C | Emergency stop |

---

## Troubleshooting

### Installation Issues

**If opencv-python fails:**
```powershell
pip install --upgrade pip
pip install opencv-python
```

**If plyer fails:**
```powershell
pip install plyer
```

### Runtime Issues

**Webcam not opening:**
- Check Windows Settings → Privacy → Camera
- Ensure no other app is using webcam
- Try running as administrator

**No notifications:**
- Turn OFF Focus Assist in Windows
- Check notification settings

**Low FPS:**
- Close other applications
- Webcam may have limited processing power

---

## File Reference

- **shoulder_surfing_opencv_monitor.py** - Main program
- **OPENCV_MONITOR_README.md** - Full documentation
- **requirements_opencv.txt** - Dependencies

---

## What's Different from Face Recognition Version?

| OpenCV Version | Face Recognition Version |
|----------------|-------------------------|
| Detects any faces/people | Distinguishes owner vs stranger |
| Simple installation | Complex installation (dlib) |
| Faster (25-30 FPS) | Slower (15-20 FPS) |
| Smaller footprint | Large dependencies |
| No owner registration | Requires owner registration |

---

## Performance Tips

**For Better Speed:**
- Close other programs
- Use good lighting
- Position yourself centered in frame

**For Better Accuracy:**
- Good room lighting
- Camera at eye level
- Clear background

---

## Next Steps

1. **Test the system** with different scenarios
2. **Adjust sensitivity** if too many false alerts
3. **Customize colors** and messages
4. **See full documentation** in OPENCV_MONITOR_README.md

---

**You're ready to detect shoulder surfing!** 🔒

Press Q to exit when done.
