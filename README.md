# 👁️ V.E.D.A. — Visual Enhancement & Digital Assistant

> **"Empowering the visually impaired with real-time AI-powered navigation, currency detection, and text reading."**

A hackathon project built to assist visually impaired individuals using a camera, AI, and voice — all running locally on a Windows machine.

---

## 🚀 What is VEDA?

VEDA is an all-in-one AI assistant that uses a smartphone or laptop camera to understand the world and speak it out loud. It has three core modes:

| Mode | What It Does |
|---|---|
| 🧭 Navigation | Detects objects & people in real-time, warns user of obstacles by voice |
| 💵 Currency | Identifies Indian currency notes and announces the denomination |
| 📖 Text Reader | Reads printed text from books, signs, or documents out loud |
| 🎙️ Voice Control | Activate any mode completely hands-free using voice commands |

---

## ✨ Features

- 🎯 **Real-time Object Detection** — YOLOv8-powered obstacle detection with distance estimation
- 🚨 **Smart Priority Voice System** — Emergency stops, navigation warnings, and info alerts on separate priority queues
- 💰 **Currency Recognition** — Majority-vote buffering for high-accuracy note detection
- 📝 **OCR Text Reader** — Tesseract + OpenCV preprocessing reads text from the real world
- 🎙️ **Voice Command Control** — Fully hands-free menu using SpeechRecognition
- 📡 **WiFi + USB Camera Support** — Works with DroidCam (phone as webcam) or laptop webcam
- 🔊 **Windows VBScript Voice Engine** — Reliable SAPI5 voice that cannot be blocked by Python threading

---

## 🗂️ Project Structure

```
VEDA/
│
├── veda.py              # 🏠 Main menu — entry point of the system
├── veda_nav.py          # 🧭 Navigation mode — YOLO object detection + voice warnings
├── currency_scan.py     # 💵 Currency detection — YOLO classification + majority vote
├── text_reader.py       # 📖 OCR text reader — Tesseract + YOLOv8 guidance
├── voice_command.py     # 🎙️ Voice-activated menu controller
│
├── models/
│   ├── veda_obj.pt      # Custom YOLO model for navigation objects
│   └── currency.pt      # Custom YOLO model for Indian currency
│
├── audio/
│   └── currency_voice.vbs   # VBScript voice engine for currency module
│
├── yolov8n.pt           # Base YOLOv8 nano model (fallback)
├── speech_engine.vbs    # Windows SAPI5 voice driver
├── veda_speech.vbs      # Navigation voice driver
└── requirements.txt
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Object Detection | YOLOv8 (Ultralytics) |
| OCR | Tesseract + pytesseract |
| Computer Vision | OpenCV |
| Voice Output | Windows SAPI5 via VBScript |
| Voice Input | SpeechRecognition + Google API |
| Distance Estimation | Focal Length Formula |
| Object Tracking | Custom IoU-based Smart Tracker |

---

## 📦 Installation

**1. Clone the repository**
```bash
git clone https://github.com/RaviChandra260/VEDA.git
cd VEDA
```

**2. Install Python dependencies**
```bash
pip install -r requirements.txt
```

**3. Install Tesseract OCR** (for Text Reader mode)
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install to: `C:\Program Files\Tesseract-OCR\`

**4. Run VEDA**
```bash
python veda.py
```

---

## 📋 Requirements

```
ultralytics
opencv-python
pytesseract
pyttsx3
speechrecognition
numpy
pyaudio
```

---

## 🎙️ Voice Commands

| Say This | Action |
|---|---|
| "Navigation" / "Activate Navigation" | Starts Navigation Mode |
| "Currency" / "Money" | Starts Currency Detection |
| "Terminate" / "Exit" | Shuts down VEDA |

---

## 🧭 How Navigation Works

```
Camera captures frame
        ↓
YOLOv8 detects objects
        ↓
Distance estimated using Focal Length formula
        ↓
Smart Tracker assigns IDs & smooths distances
        ↓
Decision Engine checks danger zones
        ↓
Priority Voice System announces:
  🔴 "Stop! Person Close!"     (Priority 0 — Emergency)
  🟡 "Veer Left"               (Priority 1 — Navigation)
  🟢 "Path Clear"              (Priority 2 — Info)
```

---

## 💵 How Currency Detection Works

```
Camera captures frame
        ↓
Image sharpening filter applied
        ↓
YOLOv8 classification model runs
        ↓
15-frame majority vote buffer
        ↓
80% consensus required before speaking
        ↓
"500 Rupees" announced via voice
```

---

## 📷 Camera Setup

VEDA supports two camera modes:

```python
# WiFi Camera (DroidCam App on phone)
DROIDCAM_URL = "http://<your-phone-ip>:4747/video"

# USB / Laptop Webcam
cap = cv2.VideoCapture(0)  # Change to 1 if 0 doesn't work
```

When you run VEDA, you'll be asked to choose:
```
[1] WiFi Camera (DroidCam)
[2] USB / Laptop Webcam
```

---

## 👨‍💻 Author

**RaviChandra260**
GitHub: [@RaviChandra260](https://github.com/RaviChandra260)

---

## 🏆 Built For

> Hackathon Project — AI for Social Good
> Designed to assist the **visually impaired** using affordable, offline-first AI.

---

## 📄 License

MIT License — free to use, modify and distribute.
