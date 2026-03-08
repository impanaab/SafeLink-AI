# SafeLink AI - Face Recognition Security System

## Overview
SafeLink AI is an advanced shoulder surfing detection system that uses face recognition to identify when strangers are looking at your screen. It distinguishes between the registered owner and unknown persons, sending alerts and visual warnings when potential threats are detected.

---

## Features

### 1. **Owner Registration**
- Captures and stores the owner's face on first run
- Uses face recognition to create a unique face encoding
- Saved as `owner_face.jpg` for future sessions

### 2. **Background Monitoring**
- Runs continuously in the background using threading
- Monitors webcam for faces every 0.5 seconds
- Low CPU usage with optimized frame processing

### 3. **Face Recognition**
- Uses `face_recognition` library (built on dlib)
- Compares detected faces against stored owner encoding
- Tolerance set to 0.6 for accurate matching

### 4. **Desktop Notifications**
- Triggers notification when stranger is detected
- Message: "⚠ Possible Shoulder Surfing Detected"
- Uses Windows notification system via `plyer`

### 5. **Visual Security Monitor**
- Opens webcam window automatically when threat detected
- **Green box** → Owner (safe)
- **Red box** → Unknown person (threat)
- Alert banner at top of screen

### 6. **Smart Alerts**
- 30-second cooldown to prevent notification spam
- Automatic monitor opening when strangers appear
- Manual monitor access via 'M' command

---

## Requirements

### Python Version
- Python 3.11 (as specified)

### Required Libraries
Install all dependencies:

```powershell
pip install opencv-python numpy face_recognition flask plyer cmake dlib
```

**Note:** `face_recognition` requires `cmake` and `dlib`. On Windows, this may require Visual Studio Build Tools.

### Alternative Installation (if face_recognition fails)
If you encounter issues installing `face_recognition` on Windows:

1. Install CMake:
   ```powershell
   pip install cmake
   ```

2. Install dlib (precompiled wheel):
   ```powershell
   pip install dlib
   ```

3. Then install face_recognition:
   ```powershell
   pip install face_recognition
   ```

---

## Installation

1. **Clone or download** the project to your Windows laptop

2. **Navigate to project folder:**
   ```powershell
   cd c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI
   ```

3. **Install dependencies:**
   ```powershell
   pip install opencv-python numpy face_recognition flask plyer
   ```

4. **Verify webcam access:**
   - Ensure your webcam is connected and working
   - Check Windows Privacy Settings → Camera → Allow apps to access camera

---

## Usage

### First Run - Owner Registration

1. **Start the program:**
   ```powershell
   python safelink_ai_face_recognition.py
   ```

2. **Register your face:**
   - Position yourself in front of the webcam
   - Press **SPACE** to capture your face
   - Press **ESC** to cancel

3. **Confirmation:**
   - You'll see: "✅ Owner registered successfully!"
   - Your face is saved as `owner_face.jpg`

### Normal Operation

Once registered, the program automatically:
1. Loads your face encoding
2. Starts background monitoring
3. Waits for commands

**Commands:**
- `M` - Manually open security monitor
- `Q` - Quit SafeLink AI

### When Threat Detected

1. **Desktop notification appears:**
   - "⚠ Possible Shoulder Surfing Detected"
   - "Another person is looking at your screen."

2. **Webcam monitor opens automatically:**
   - Green box around your face (Owner)
   - Red box around stranger's face (Unknown)
   - Red banner: "⚠ WARNING: SHOULDER SURFING DETECTED"

3. **Close monitor:**
   - Press `Q` in the webcam window

---

## Auto-Start at Windows Startup

### Method 1: Startup Folder (Recommended)

1. **Create a batch file** to start SafeLink AI:
   
   Create file: `start_safelink.bat`
   ```batch
   @echo off
   cd /d "c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI"
   python safelink_ai_face_recognition.py
   ```

2. **Open Windows Startup folder:**
   - Press `Win + R`
   - Type: `shell:startup`
   - Press Enter

3. **Copy the batch file** to the Startup folder

4. **Test:**
   - Restart your computer
   - SafeLink AI should start automatically

### Method 2: Task Scheduler (Advanced)

1. **Open Task Scheduler:**
   - Press `Win + R`
   - Type: `taskschd.msc`
   - Press Enter

2. **Create Basic Task:**
   - Name: `SafeLink AI`
   - Trigger: `When I log on`
   - Action: `Start a program`
   - Program: `C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe`
   - Arguments: `safelink_ai_face_recognition.py`
   - Start in: `c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI`

3. **Configure:**
   - Check "Run with highest privileges"
   - Set to run only when user is logged on

4. **Test:**
   - Right-click the task → Run
   - Verify SafeLink AI starts

### Method 3: Registry (Expert Only)

1. **Open Registry Editor:**
   - Press `Win + R`
   - Type: `regedit`
   - Navigate to: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`

2. **Add new String Value:**
   - Name: `SafeLinkAI`
   - Value: `"C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe" "c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI\safelink_ai_face_recognition.py"`

3. **Restart** to test

---

## How It Works

### Detection Logic

```python
for each detected face:
    compare with owner encoding
    
    if match found:
        label = "Owner"
        color = Green (0, 255, 0)
    else:
        label = "Unknown"
        color = Red (0, 0, 255)
        trigger_alert()

if stranger_count > 0 OR total_faces > 1:
    display "⚠ SHOULDER SURFING DETECTED"
else:
    display "SAFE - No Threat Detected"
```

### Performance Optimization

- **Frame resizing:** 50% scale for faster processing
- **Background thread:** Monitoring runs asynchronously
- **Alert cooldown:** 30 seconds between notifications
- **Low resolution capture:** 640x480 for monitoring

---

## Troubleshooting

### Webcam Not Detected
- Check Windows Device Manager
- Verify camera permissions in Windows Settings
- Try different USB port
- Restart the program

### Face Recognition Installation Failed
```powershell
# Install Visual Studio Build Tools first
# Then install with:
pip install --upgrade cmake
pip install dlib
pip install face_recognition
```

### Notifications Not Showing
- Check Windows notification settings
- Ensure "Focus Assist" is OFF
- Try running as administrator

### False Positives
- Re-register your face in better lighting
- Adjust tolerance in code (line 129): `tolerance=0.6` → `tolerance=0.5`

### High CPU Usage
- Increase sleep interval in background_monitor (line 198): `time.sleep(0.5)` → `time.sleep(1.0)`
- Reduce frame processing frequency

---

## File Structure

```
SafeLinkAI/
│
├── safelink_ai_face_recognition.py   # Main program
├── owner_face.jpg                     # Stored owner face (auto-generated)
├── FACE_RECOGNITION_README.md         # This file
└── start_safelink.bat                 # Startup script
```

---

## Security Notes

1. **Owner face data** is stored locally (not cloud-based)
2. **No network communication** - all processing is offline
3. **Webcam access** only when program is running
4. **Delete `owner_face.jpg`** to reset and re-register

---

## Commands Summary

| Command | Action |
|---------|--------|
| `SPACE` | Capture owner face (during registration) |
| `ESC` | Cancel registration |
| `M` | Manually open security monitor |
| `Q` | Quit SafeLink AI |
| `Q` (in monitor) | Close webcam window |
| `CTRL+C` | Emergency stop |

---

## Advanced Customization

### Adjust Detection Sensitivity
Edit line 129 in `safelink_ai_face_recognition.py`:
```python
matches = face_recognition.compare_faces([self.owner_encoding], face_encoding, tolerance=0.6)
# tolerance: Lower = stricter (0.4-0.5), Higher = lenient (0.6-0.7)
```

### Change Alert Cooldown
Edit line 183:
```python
alert_cooldown = 30  # Seconds between alerts (default: 30)
```

### Modify Monitoring Interval
Edit line 198:
```python
time.sleep(0.5)  # Check every 0.5 seconds (default)
```

---

## License
SafeLink AI - Educational cybersecurity prototype

## Support
For issues or questions, review the troubleshooting section or check library documentation:
- OpenCV: https://docs.opencv.org/
- face_recognition: https://github.com/ageitgey/face_recognition

---

**Stay Safe with SafeLink AI! 🔒**
