import cv2
import os
import time
import threading
import numpy as np
from ultralytics import YOLO

# ================= CONFIGURATION =================
DROIDCAM_URL = "http://10.20.189.101:4747/video"
MODEL_PATH = "models/currency.pt"

# Strictness settings
CONFIDENCE_THRESHOLD = 0.94     # High confidence required
BUFFER_SIZE = 15                # Frames to check for stability
SPEAK_COOLDOWN = 4.0            # Time between voice outputs
# =================================================

VBS_FILE = "audio/currency_voice.vbs"

def setup_voice_engine():
    if not os.path.exists("audio"): os.makedirs("audio")
    if not os.path.exists(VBS_FILE):
        with open(VBS_FILE, "w") as f:
            f.write('Set Sapi = Wscript.CreateObject("SAPI.SpVoice")\n')
            f.write('Sapi.Rate = 1\n')
            f.write('Sapi.Speak Wscript.Arguments(0)')

def speak(text):
    def _run():
        try:
            # Create the VBS file if missing
            setup_voice_engine()
            clean_text = text.replace('"', '')
            os.system(f'cscript //Nologo {VBS_FILE} "{clean_text}"')
        except Exception as e:
            print(f"Voice Error: {e}")
    threading.Thread(target=_run, daemon=True).start()

def start_currency(cam_mode="wifi"):
    setup_voice_engine()
    print(f"Loading Currency Model...")
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"❌ Error: Model not found at {MODEL_PATH}")
        return

    # --- CAMERA SELECTION LOGIC ---
    cap = None
    
    if cam_mode == "wifi":
        print(f"Connecting to WiFi Camera: {DROIDCAM_URL}")
        cap = cv2.VideoCapture(DROIDCAM_URL)
        if not cap.isOpened():
            print("⚠️ WiFi Camera failed. Switching to USB...")
            cam_mode = "usb" # Fallback

    if cam_mode == "usb":
        print("Connecting to USB / Laptop Camera...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            cap = cv2.VideoCapture(1) # Try external USB if internal fails

    if not cap or not cap.isOpened():
        print("❌ CRITICAL ERROR: No Camera Found")
        return

    cap.set(3, 1280)
    cap.set(4, 720)
    
    # --- DETECTION VARIABLES ---
    detection_buffer = []
    last_speak_time = 0
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]) # Sharpening

    print("✅ Currency Scanner Active. Press 'q' to Return to Menu.")
    speak("Currency Mode Active")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Image Enhancement
        frame = cv2.filter2D(frame, -1, kernel)

        # Run AI
        results = model(frame, verbose=False)
        
        status_text = "Scanning..."
        color = (0, 0, 255) 

        if results and results[0].probs:
            top_index = results[0].probs.top1
            confidence = results[0].probs.top1conf.item()
            raw_name = results[0].names[top_index]
            
            # --- CRITICAL FIX: IGNORE BACKGROUND ---
            if raw_name.lower() == "background":
                raw_name = "None"

            # 1. Fill buffer: If low confidence, record "None"
            if confidence > CONFIDENCE_THRESHOLD:
                detection_buffer.append(raw_name)
            else:
                detection_buffer.append("None")

            # Keep buffer at fixed size
            if len(detection_buffer) > BUFFER_SIZE:
                detection_buffer.pop(0)

            # 2. Majority Vote Logic
            # Only speak if the SAME currency appears in 80% of recent frames
            if detection_buffer.count(raw_name) > (BUFFER_SIZE * 0.8) and raw_name != "None":
                display_name = raw_name.replace("_", " ").title()
                
                # Double check to ensure we don't say "Background Rupees"
                if "background" not in display_name.lower():
                    if "Rupees" not in display_name: 
                        display_name += " Rupees"
                    
                    status_text = f"{display_name} ({int(confidence * 100)}%)"
                    color = (0, 255, 0) 

                    current_time = time.time()
                    if current_time - last_speak_time > SPEAK_COOLDOWN:
                        print(f"🎤 Speaking: {display_name}")
                        speak(display_name)
                        last_speak_time = current_time

        # UI Drawing
        cv2.rectangle(frame, (0, 0), (640, 60), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        cv2.imshow("Currency Assistant", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

# This ensures it can run standalone for testing
if __name__ == "__main__":
    start_currency()