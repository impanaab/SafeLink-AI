# SafeLink AI - Quick Start Guide

## ⚡ 30-Second Setup

### 1. Start Backend (Terminal)
```bash
cd c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI
python safelink_monitor.py
```

### 2. Load Extension (Chrome)
1. Open: `chrome://extensions/`
2. Enable "Developer mode" (top-right)
3. Click "Load unpacked"
4. Select: `c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI\safelink_extension`

### 3. Test (Browser)
1. Go to: `https://github.com/login`
2. Camera window opens automatically
3. See green box (SAFE) or red box (THREAT)
4. Press Q to close camera window

---

## 📂 Files Created

| File | Purpose |
|------|---------|
| **safelink_monitor.py** | Main Flask backend + camera monitoring |
| **safelink_extension/manifest.json** | Extension configuration |
| **safelink_extension/content.js** | Password field detection |
| **safelink_extension/background.js** | Extension service worker |
| **safelink_extension/popup.html** | Extension UI + status |
| **SAFELINK_COMPLETE_SETUP.md** | Detailed setup guide (THIS FILE) |

---

## 🎯 How It Works

```
[Browser: github.com/login]
           ↓
[Extension detects password field]
           ↓
[POST http://127.0.0.1:5001/activate]
           ↓
[Python Backend receives signal]
           ↓
[Camera window opens]
           ↓
[Face detection starts]
           ↓
[SAFE or ⚠ SHOULDER SURFING DETECTED]
```

---

## ✅ System Features

- ✅ Automatic login page detection (all sites)
- ✅ Real-time camera activation
- ✅ Haar Cascade face detection
- ✅ Color-coded alerts (green/red)
- ✅ Live FPS counter
- ✅ Multi-tab support
- ✅ Press Q to stop
- ✅ 30 FPS target performance
- ✅ No cloud/external calls
- ✅ Fully documented code

---

## 🚀 Demo Commands

```bash
# Start the backend
python safelink_monitor.py

# Check if port 5001 is available
netstat -ano | findstr :5001

# Test face detection
python -c "import cv2; print('Camera OK')"
```

---

## 🔗 Test URLs

Click these after loading the extension:
- `https://github.com/login`
- `https://accounts.google.com`
- `https://www.linkedin.com/login`
- `https://login.live.com`
- `https://www.amazon.com/ap/signin`

---

## ⚠️ If Camera Doesn't Open

1. **Check Python backend is running** - Make sure terminal shows "Listening for browser activation signals"
2. **Check camera permissions** - Windows Settings → Privacy → Camera
3. **Check firewall** - Port 5001 might be blocked
4. **Close other apps** - Zoom, Teams might be using camera

---

## 📊 Expected Output

**Backend Terminal:**
```
[SafeLink AI] Background protection active
[SafeLink AI] Listening for browser activation signals...
[SafeLink AI] Login page detected. Activating camera monitoring.
[SafeLink AI] Camera monitoring started
[SafeLink AI] Camera initialized successfully
```

**Camera Window:**
- Green banner: "SAFE – No Threat Detected"
- Red banner: "⚠ SHOULDER SURFING DETECTED"
- Face count display
- FPS counter (top-right)

---

**System Ready! Start with: `python safelink_monitor.py`**
