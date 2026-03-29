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
CONFIDENCE_THRESHOLD = 0.98     # Increased for even higher accuracy
BUFFER_SIZE = 15                # Number of frames to check
SPEAK_COOLDOWN = 5.0           
# =================================================

VBS_FILE = "speech_engine.vbs"

def setup_voice_engine():
    if not os.path.exists(VBS_FILE):
        with open(VBS_FILE, "w") as f:
            f.write('Set Sapi = Wscript.CreateObject("SAPI.SpVoice")\n')
            f.write('Sapi.Rate = 1\n')
            f.write('Sapi.Speak Wscript.Arguments(0)')

def speak(text):
    def _run():
        try:
            clean_text = text.replace('"', '')
            os.system(f'cscript //Nologo {VBS_FILE} "{clean_text}"')
        except Exception as e:
            print(f"Voice Error: {e}")
    threading.Thread(target=_run, daemon=True).start()

def main():
    setup_voice_engine()
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    cap = cv2.VideoCapture(DROIDCAM_URL)
    
    # --- MAJORITY VOTE DETECTION SYSTEM ---
    detection_buffer = []
    last_speak_time = 0
    last_spoken = ""

    # Sharpening Kernel to help the AI see texture
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

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
            
            # 1. Fill buffer: If low confidence, record "None" to block false alarms
            if confidence > CONFIDENCE_THRESHOLD:
                detection_buffer.append(raw_name)
            else:
                detection_buffer.append("None")

            # Keep buffer at fixed size
            if len(detection_buffer) > BUFFER_SIZE:
                detection_buffer.pop(0)

            # 2. Only speak if the SAME currency appears in 80% of recent frames
            # This ignores "flickeraing" 500-rupee detections on your laptop screen.
            if detection_buffer.count(raw_name) > (BUFFER_SIZE * 0.8) and raw_name != "None":
                display_name = raw_name.replace("_", " ").title()
                if "Rupees" not in display_name: 
                    display_name += " Rupees"
                
                status_text = f"{display_name} ({int(confidence * 100)}%)"
                color = (0, 255, 0) 

                current_time = time.time()
                # Check cooldown and ensure we aren't repeating the same name immediately
                if current_time - last_speak_time > SPEAK_COOLDOWN:
                    print(f"🎤 Confirmed: {display_name}")
                    speak(display_name)
                    last_speak_time = current_time

        # UI Drawing
        cv2.rectangle(frame, (0, 0), (640, 60), (0, 0, 0), -1)
        cv2.putText(frame, status_text, (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        cv2.imshow("Currency Assistant (Strict Majority Mode)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()