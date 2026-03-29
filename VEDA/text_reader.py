import cv2
import pytesseract
import pyttsx3
import numpy as np
import threading
import queue
import time
import os
import re
from ultralytics import YOLO

# --- CONFIGURATION ---
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
DROIDCAM_URL = "http://10.20.189.101:4747/video"

# --- VOICE ENGINE ---
speech_queue = queue.Queue()

def speech_worker():
    while True:
        text = speech_queue.get()
        if text is None: break
        try:
            # Re-init to prevent freezing
            engine = pyttsx3.init('sapi5')
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
            del engine
        except: pass
        finally:
            speech_queue.task_done()

voice_thread = threading.Thread(target=speech_worker, daemon=True)
voice_thread.start()

def speak(text, urgent=False):
    if urgent:
        with speech_queue.mutex:
            speech_queue.queue.clear()
    speech_queue.put(text)

def preprocess_for_ocr(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 31, 15)
    return cv2.medianBlur(binary, 3)

def start_reader(cam_mode="wifi"):
    print("Loading AI Brain...")
    
    # --- 1. ROBUST MODEL LOADING ---
    # We try standard YOLOv8n instead of a custom model
    try:
        model = YOLO('yolov8n.pt') 
        print("✅ Standard AI Loaded (Looking for Books)")
    except:
        print("⚠️ Warning: No AI Model found. Running in Manual Mode.")
        model = None

    # --- 2. CAMERA SETUP ---
    cap = None
    if cam_mode == "wifi":
        print(f"Connecting to WiFi Camera: {DROIDCAM_URL}")
        cap = cv2.VideoCapture(DROIDCAM_URL)
        if not cap.isOpened():
            print("⚠️ WiFi Camera failed. Switching to USB...")
            cam_mode = "usb" 

    if cam_mode == "usb":
        cap = cv2.VideoCapture(0)
        if not cap.isOpened(): cap = cv2.VideoCapture(1)

    if not cap or not cap.isOpened():
        print("❌ CRITICAL ERROR: No Camera Found")
        input("Press Enter to return...")
        return

    speak("Reader Mode Active. Show me text.")
    print("✅ Text Reader Active. Press 'q' to Return.")

    # Variables
    stable_frames = 0
    busy_until = 0 
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        display = frame.copy()
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        
        # Draw the "Scan Zone" Box
        box_w, box_h = int(w*0.8), int(h*0.4)
        bx1, by1 = cx - box_w//2, cy - box_h//2
        bx2, by2 = cx + box_w//2, cy + box_h//2
        
        current_time = time.time()
        
        # --- PHASE 0: BUSY WAIT ---
        if current_time < busy_until:
            remaining = int(busy_until - current_time)
            cv2.rectangle(display, (0, h-60), (w, h), (0,0,0), -1)
            cv2.putText(display, f"READING... {remaining}s", (20, h-20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.imshow("Text Reader", display)
            if cv2.waitKey(1) & 0xFF == ord('q'): break
            continue 

        # --- PHASE 1: GUIDANCE (Using YOLO if available) ---
        target_box = None
        
        if model:
            # Look for books (Class 73 in COCO dataset)
            results = model(frame, verbose=False, classes=[73]) 
            max_area = 0
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    area = (x2-x1)*(y2-y1)
                    if area > max_area:
                        max_area = area
                        target_box = (x1, y1, x2, y2)

        # --- PHASE 2: LOGIC ---
        color = (0, 255, 0) # Default Green
        instruction = "Hold Steady"
        
        if target_box:
            # If AI sees a book, guide user to center it
            tx1, ty1, tx2, ty2 = target_box
            tcx, tcy = (tx1+tx2)//2, (ty1+ty2)//2
            
            cv2.rectangle(display, (tx1, ty1), (tx2, ty2), (255, 0, 0), 2)
            
            if tcx < cx - 100: instruction = "Move Left"
            elif tcx > cx + 100: instruction = "Move Right"
            elif tcy < cy - 100: instruction = "Move Up"
            elif tcy > cy + 100: instruction = "Move Down"
            else: instruction = "Perfect. Hold Steady."
            
        else:
            # If no AI detection, just use the center box
            instruction = "Place Text in Box"
        
        # --- PHASE 3: STABILITY & READING ---
        if "Steady" in instruction or "Box" in instruction:
            stable_frames += 1
            # Progress Bar
            progress = int((stable_frames / 20) * (bx2-bx1))
            cv2.rectangle(display, (bx1, by2+10), (bx1+progress, by2+20), (0,255,0), -1)
            
            if stable_frames > 20: # ~1 second of holding still
                speak("Capturing...", urgent=True)
                
                # Crop the center box area
                roi = frame[by1:by2, bx1:bx2]
                
                # Image Processing
                processed = preprocess_for_ocr(roi)
                text = pytesseract.image_to_string(processed)
                
                # Cleanup Text
                clean_text = re.sub(r'[^a-zA-Z0-9\s,.]', '', text).strip()
                
                if len(clean_text) > 5:
                    print(f"📖 READ: {clean_text}")
                    speak(clean_text)
                    # Wait time depends on text length
                    wait_time = max(3, len(clean_text.split()) / 2.5)
                    busy_until = time.time() + wait_time
                else:
                    speak("Text unclear", urgent=True)
                
                stable_frames = 0
        else:
            stable_frames = 0
            # Only speak guidance occasionally
            if int(time.time()) % 3 == 0:
                 speak(instruction, urgent=True)

        # Draw UI
        cv2.rectangle(display, (bx1, by1), (bx2, by2), color, 2)
        cv2.putText(display, instruction, (bx1, by1-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Text Reader", display)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_reader()