# 🛡️ SafeLink AI – Multi-Layer Threat Detection System

**A real-time cybersecurity solution detecting Evil Twin WiFi attacks and Shoulder Surfing threats**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-red.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Demo](#-demo)
- [Future Enhancements](#-future-enhancements)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚨 Problem Statement

In today's hyper-connected world, users face sophisticated cybersecurity threats:

### 1. **Evil Twin WiFi Attacks**
Attackers create fake WiFi access points with identical SSIDs (network names) to legitimate networks, tricking users into connecting to malicious networks. This allows attackers to:
- Intercept sensitive data (passwords, credit cards, emails)
- Perform man-in-the-middle attacks
- Deploy malware

### 2. **Shoulder Surfing Attacks**
Visual hacking where attackers observe victims' screens in public spaces (cafes, airports, libraries) to steal:
- Login credentials
- Banking information
- Confidential documents
- Personal data

**Current Gap:** Most security tools focus on digital threats but ignore physical surveillance and network-layer deceptions.

---

## 💡 Solution

**SafeLink AI** is an intelligent, multi-layer threat detection system that provides:

✅ **Real-time Evil Twin WiFi Detection** - Identifies duplicate network SSIDs with different MAC addresses  
✅ **Webcam-Based Shoulder Surfing Detection** - Uses computer vision to detect unauthorized viewers  
✅ **User-Friendly Dashboard** - Intuitive web interface with instant security alerts  
✅ **Local Processing** - Complete privacy - no data sent to external servers  
✅ **Cross-Platform** - Works on Windows, macOS, and Linux  

---

## ✨ Features

### 🌐 Network Security Module
- **Real Live WiFi Scanning**: Scans actual WiFi networks using Windows netsh command
- **Evil Twin WiFi Detection**: Identifies suspicious duplicate SSIDs with different BSSIDs
- **MAC Address Verification**: Cross-references network names with hardware addresses
- **Real-time Alerts**: Instant warnings when threats are detected

### 👁️ Visual Privacy Module
- **Face Detection**: Uses OpenCV Haar Cascade for accurate face detection
- **Multi-Person Detection**: Identifies when multiple people are near your screen
- **Webcam Integration**: Automatically processes video frames
- **Privacy-First**: All processing happens locally on your device

### 🎨 User Interface
- **Modern Cybersecurity Dashboard**: Dark-themed, professional interface
- **Color-Coded Alerts**: Green (Safe) / Red (Threat Detected)
- **One-Click Scanning**: Simple button to trigger comprehensive security check
- **Responsive Design**: Works on desktop, tablet, and mobile browsers

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.8+** | Core programming language |
| **Flask** | Web framework for backend API |
| **OpenCV** | Computer vision for face detection |
| **NumPy** | Numerical operations and array processing |
| **Scapy** | Network packet manipulation (for WiFi scanning) |
| **HTML5/CSS3** | Frontend dashboard interface |
| **JavaScript** | Dynamic UI interactions |

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Webcam (for shoulder surfing detection)
- Administrator/root privileges (for WiFi scanning in production)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/SafeLinkAI.git
cd SafeLinkAI
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt includes:**
- flask
- opencv-python
- numpy
- scapy

### Step 3: Verify Installation
```bash
python -c "import cv2; import flask; import numpy; print('All dependencies installed successfully!')"
```

---

## 🚀 Usage

### Starting the Application

1. **Navigate to the project directory:**
   ```bash
   cd SafeLinkAI
   ```

2. **Run the Flask server:**
   ```bash
   python app.py
   ```

3. **Open your web browser and visit:**
   ```
   http://127.0.0.1:5000
   ```

### Running a Security Scan

1. Click the **"🔍 Run Security Scan"** button on the dashboard
2. Grant webcam permissions when prompted (required for shoulder surfing detection)
3. Wait for the scan to complete (~10-15 seconds)
4. View results in the two security panels:
   - **📡 Network Security**: WiFi threat status
   - **👁️ Visual Privacy**: Shoulder surfing status

### Interpreting Results

#### ✅ Safe Status (Green)
```
✓ No suspicious WiFi networks detected. All networks appear legitimate.
✓ No shoulder surfing detected. You appear to be working alone.
```

#### ⚠️ Threat Detected (Red)
```
⚠️ Possible Evil Twin WiFi detected! Duplicate SSIDs found: CoffeeShopWiFi
⚠️ Shoulder Surfing Risk Detected! Multiple people detected. Someone may be watching your screen.
```

---

## 🔍 How It Works

### Evil Twin WiFi Detection Algorithm

```python
# Step 1: Scan REAL WiFi networks using Windows 'netsh' command
# Command: netsh wlan show networks mode=bssid
# Parses SSIDs and BSSIDs (MAC addresses)

# Step 2: Group networks by SSID
# Step 3: Detect SSIDs with multiple MAC addresses
# Step 4: Flag as Evil Twin attack if duplicates found
```

**Detection Logic:**
- If SSID appears multiple times with different MAC addresses → **THREAT**
- If all SSIDs have unique MAC addresses → **SAFE**

### Shoulder Surfing Detection Algorithm

```python
# Step 1: Open webcam
# Step 2: Capture 50 frames
# Step 3: Convert frames to grayscale
# Step 4: Apply Haar Cascade face detection
# Step 5: Count faces in each frame
# Step 6: If >1 face detected consistently → RISK
```

**Detection Logic:**
- Analyzes 50 frames from webcam
- Uses OpenCV's `haarcascade_frontalface_default.xml`
- If >20% of frames show multiple faces → **RISK**
- If single/no faces detected → **SAFE**

---

## 📁 Project Structure

```
SafeLinkAI/
│
├── app.py                  # Flask backend server
├── wifi_scanner.py         # Evil Twin WiFi detection module
├── shoulder_detection.py   # Shoulder surfing detection module
├── requirements.txt        # Python dependencies
│
├── templates/
│   └── index.html         # Main dashboard UI
│
├── static/
│   └── style.css          # Dashboard styling
│
└── README.md              # Project documentation
```

### File Descriptions

| File | Purpose |
|------|---------|
| `app.py` | Flask web server with routes for dashboard and scanning |
| `wifi_scanner.py` | WiFi network scanning and Evil Twin detection logic |
| `shoulder_detection.py` | Webcam access and face detection for shoulder surfing |
| `index.html` | Interactive dashboard frontend |
| `style.css` | Cybersecurity-themed dark mode styling |
| `requirements.txt` | All Python package dependencies |

---

## 🎥 Demo

### Screenshot Preview

**Dashboard Interface:**
```
🛡️ SafeLink AI
Multi-Layer Human & Network Threat Detection System

┌─────────────────────────────────────┐
│   🔍 Run Security Scan              │
└─────────────────────────────────────┘

┌─────────────────────┬─────────────────────┐
│ 📡 Network Security │ 👁️ Visual Privacy   │
│                     │                     │
│ ✅ SAFE             │ ⚠️ THREAT DETECTED  │
│                     │                     │
│ No suspicious WiFi  │ Multiple faces      │
│ networks detected   │ detected in frame   │
└─────────────────────┴─────────────────────┘
```

---

## 🚀 Future Enhancements

### Planned Features
- [ ] **Real WiFi Scanning**: Integration with system WiFi APIs (Windows/Linux/macOS)
- [ ] **Behavioral Analysis**: Track network patterns over time
- [ ] **Alert Notifications**: Desktop/mobile push notifications
- [ ] **Logging System**: Historical threat logs with timestamps
- [ ] **ML-Based Detection**: Train models to detect suspicious behavior patterns
- [ ] **Multi-Camera Support**: Monitor multiple angles simultaneously
- [ ] **Encryption Check**: Verify if networks use WPA2/WPA3 encryption
- [ ] **VPN Integration**: Auto-enable VPN when threats detected
- [ ] **Browser Extension**: Quick access from browser toolbar

### Technical Improvements
- [ ] Docker containerization
- [ ] REST API documentation
- [ ] Unit tests and CI/CD pipeline
- [ ] Database integration for threat history
- [ ] Mobile app version (iOS/Android)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 Python style guide
- Add comments for complex logic
- Update README.md for new features
- Test thoroughly before submitting PR

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

**Your Name** - *Initial work* - [YourGitHub](https://github.com/impanaab)

---

## 🙏 Acknowledgments

- OpenCV community for excellent computer vision libraries
- Flask team for the lightweight web framework
- Hackathon organizers for the opportunity
- All contributors and testers

---

## 📞 Contact

For questions, suggestions, or collaboration:

- **Email**: impanaab65@gmail.com
- **GitHub**: [@yourusername](https://github.com/impanaab)
- **LinkedIn**: [Your Name](https://linkedin.com/in/impanaab)

---

## ⚠️ Disclaimer

This tool is designed for **educational and ethical security testing purposes only**. 

- Always obtain proper authorization before scanning networks
- Respect privacy laws and regulations
- Use webcam detection responsibly
- This is a proof-of-concept for hackathon demonstration

**The developers are not responsible for any misuse of this software.**

---

<div align="center">

**Built with ❤️ for Hackathon 2026**

⭐ Star this repo if you find it useful! ⭐

</div>
