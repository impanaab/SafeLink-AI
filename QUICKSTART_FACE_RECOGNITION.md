# SafeLink AI - Quick Start Guide

## 30-Second Setup

### 1. Install Dependencies
```powershell
cd c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI
pip install -r requirements_face_recognition.txt
```

**Note:** If `face_recognition` installation fails, install components separately:
```powershell
pip install cmake
pip install dlib
pip install face_recognition
```

### 2. Run SafeLink AI
```powershell
python safelink_ai_face_recognition.py
```

### 3. Register Your Face
- Webcam opens automatically
- Position yourself in frame
- Press **SPACE** to capture
- Registration complete!

### 4. Monitoring Active
- SafeLink AI now runs in background
- Detects strangers automatically
- Sends alerts when threats detected

---

## How It Works

1. **Owner Registration**
   - Your face is captured and encoded
   - Stored locally as `owner_face.jpg`

2. **Background Monitoring**
   - Continuously scans for faces
   - Compares against your registered face

3. **Threat Detection**
   - Green box = You (Owner)
   - Red box = Stranger (Threat)
   - Notification sent when stranger appears

4. **Visual Alert**
   - Webcam monitor opens automatically
   - Shows real-time threat status
   - Press Q to close

---

## Auto-Start at Boot

### Simple Method:
1. Press `Win + R`
2. Type: `shell:startup`
3. Copy `start_safelink.bat` to this folder
4. Restart computer - SafeLink AI starts automatically!

---

## Commands

| Key | Action |
|-----|--------|
| `SPACE` | Capture face (during registration) |
| `M` | Open monitor manually |
| `Q` | Quit program |
| `ESC` | Cancel registration |

---

## Test the System

1. **Run the program**
2. **Sit in front of camera alone** → Green box, "SAFE" message
3. **Have someone stand behind you** → Red box, alert notification
4. **Webcam monitor opens** → Shows threat warning

---

## Troubleshooting

### Can't install face_recognition?
**Solution:** Need Visual Studio Build Tools
- Download: https://visualstudio.microsoft.com/downloads/
- Install "Desktop development with C++"
- Then retry: `pip install face_recognition`

### Webcam not working?
**Solution:** Check Windows permissions
- Settings → Privacy → Camera
- Enable camera access for apps

### No notifications?
**Solution:** Check Focus Assist
- Settings → System → Focus Assist → Turn OFF

---

**You're all set! SafeLink AI is protecting you from shoulder surfing.** 🔒
