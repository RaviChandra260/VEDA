import cv2
from ultralytics import YOLO
import threading
import time
import queue
import os
import subprocess
import numpy as np

# ==========================================
#       STAGE 1: CONFIGURATION
# ==========================================

DROIDCAM_URL = "http://10.20.189.101:4747/video"

# SETTINGS
SKIP_FRAMES = 2              
CONFIDENCE_THRESHOLD = 0.55  
IOU_THRESHOLD = 0.45          
FOCAL_LENGTH = 650  

# OBJECT DATA
REAL_WIDTHS = {
    "person": 0.50, "bicycle": 0.45, "car": 1.80, "motorcycle": 0.80, 
    "bus": 2.50, "truck": 2.50, "traffic light": 0.30, "stop sign": 0.75,
    "bench": 1.50, "cat": 0.15, "dog": 0.25, "chair": 0.50, "potted plant": 0.40
}

# ==========================================
#       STAGE 2: ROBUST VBSCRIPT VOICE
# ==========================================
# This method uses Windows native scripting. It CANNOT be blocked by Python.
VBS_FILE = "veda_speech.vbs"

def setup_voice_driver():
    """Creates a standalone VBScript file for reliable audio."""
    if not os.path.exists(VBS_FILE):
        with open(VBS_FILE, "w") as f:
            f.write('Set Sapi = Wscript.CreateObject("SAPI.SpVoice")\n')
            f.write('Sapi.Rate = 1\n')  # Speed: 0 is normal, 2 is fast
            f.write('Sapi.Volume = 100\n')
            f.write('Sapi.Speak Wscript.Arguments(0)')

class VoiceManager:
    def __init__(self):
        self.queue = queue.PriorityQueue()
        self.running = True
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.thread.start()
        
        # Timers to prevent stuttering
        self.last_urgent_time = 0
        self.last_nav_time = 0
        self.last_info_time = 0
        
        # Create the driver file
        setup_voice_driver()

    def say(self, text, priority=2):
        current_time = time.time()
        
        # P0: EMERGENCY (Stop commands) - Max once every 2.0s
        if priority == 0:
            if current_time - self.last_urgent_time < 2.0: return
            with self.queue.mutex:
                self.queue.queue.clear() # Clear old messages
            self.queue.put((0, text))
            self.last_urgent_time = current_time
            return

        # P1: NAVIGATION (Veer/Move) - Max once every 1.5s
        if priority == 1:
            if current_time - self.last_nav_time < 1.5: return
            self.last_nav_time = current_time
            self.queue.put((1, text))
            return
            
        # P2: INFO (General status) - Max once every 5.0s
        if priority == 2:
            if current_time - self.last_info_time < 5.0: return
            self.last_info_time = current_time
            self.queue.put((2, text))

    def worker(self):
        print("✅ Voice System: VBScript Driver Loaded", flush=True)
        # Test Sound
        self.speak_subprocess("System Online")
        
        while self.running:
            try:
                priority, text = self.queue.get(timeout=0.5)
                
                # Print to terminal clearly
                print(f"🗣️ [SPEAKING]: {text}", flush=True)
                
                # Execute external Windows voice command
                self.speak_subprocess(text)
                
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Voice Error: {e}", flush=True)

    def speak_subprocess(self, text):
        """Runs the VBScript in a separate process to guarantee sound."""
        try:
            # Clean text for command line
            safe_text = text.replace('"', '').replace("'", "")
            subprocess.run(['cscript', '//Nologo', VBS_FILE, safe_text], check=False)
        except:
            pass

    def stop(self):
        self.running = False

# ==========================================
#       STAGE 3: TRACKER
# ==========================================
class SmartTracker:
    def __init__(self):
        self.tracked_objects = {} 
        self.next_id = 1

    def update(self, detections):
        new_tracked = {}
        for det in detections:
            best_id = -1
            best_iou = 0.0
            for obj_id, obj_data in self.tracked_objects.items():
                iou = self.calculate_iou(det['box'], obj_data['box'])
                if iou > best_iou:
                    best_iou = iou
                    best_id = obj_id
            
            if best_iou > IOU_THRESHOLD:
                # Update existing object
                prev_data = self.tracked_objects[best_id]['data']
                smoothed_dist = round((0.6 * prev_data['dist']) + (0.4 * det['dist']), 2)
                det['dist'] = smoothed_dist
                det['velocity'] = prev_data['dist'] - det['dist'] 
                new_tracked[best_id] = {'box': det['box'], 'lost_frames': 0, 'data': det}
            else:
                # New object
                det['velocity'] = 0.0 
                new_tracked[self.next_id] = {'box': det['box'], 'lost_frames': 0, 'data': det}
                self.next_id += 1
                
        # Keep lost objects briefly
        for obj_id, obj_data in self.tracked_objects.items():
            if obj_id not in new_tracked and obj_data['lost_frames'] < 5:
                obj_data['lost_frames'] += 1
                new_tracked[obj_id] = obj_data
        self.tracked_objects = new_tracked
        return new_tracked

    def calculate_iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(boxAArea + boxBArea - interArea + 1e-5)

# ==========================================
#       STAGE 4: MAIN LOGIC
# ==========================================
def draw_hud(frame, x1, y1, x2, y2, color, label):
    # Draw simple bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    # Label Background
    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
    cv2.rectangle(frame, (x1, y1 - 20), (x1 + w, y1), color, -1)
    cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 1)

def start_veda(cam_mode="wifi"):
    print("\n--- V.E.D.A. SYSTEM STARTING ---", flush=True)
    
    # --- CAMERA SETUP ---
    cap = None
    if cam_mode == "wifi":
        print(f"Connecting to WiFi: {DROIDCAM_URL}", flush=True)
        cap = cv2.VideoCapture(DROIDCAM_URL)
        if not cap.isOpened():
            print("⚠️ WiFi Failed. Switching to USB...", flush=True)
            cam_mode = "usb" 

    if cam_mode == "usb":
        print("Connecting to USB Camera...", flush=True)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened(): cap = cv2.VideoCapture(1)

    if not cap or not cap.isOpened():
        print("❌ ERROR: No Camera Found", flush=True)
        return

    # --- MODEL SETUP ---
    print("⏳ Loading AI...", flush=True)
    try: model = YOLO('models/veda_obj.pt') 
    except: model = YOLO('yolov8n.pt')

    # --- SYSTEMS SETUP ---
    tracker = SmartTracker()
    voice = VoiceManager() # Now uses VBScript (Reliable)

    width = int(cap.get(3))
    height = int(cap.get(4))
    frame_count = 0
    last_print_time = 0  # Timer to slow down terminal

    try:
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            frame_count += 1
            if frame_count % SKIP_FRAMES != 0: continue

            detections = []
            
            # Run AI (Standard mode, no streams)
            results = model(frame, verbose=False)
            
            for r in results:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    if conf > CONFIDENCE_THRESHOLD:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls_id = int(box.cls[0])
                        
                        if 0 <= cls_id < len(model.names):
                            name = model.names[cls_id]
                            
                            if name in REAL_WIDTHS:
                                w_px = x2 - x1
                                real_w = REAL_WIDTHS.get(name, 0.5)
                                dist = (real_w * FOCAL_LENGTH) / w_px if w_px > 0 else 9.9
                                if y2 > (height * 0.85): dist = min(dist, 1.2)

                                detections.append({
                                    'box': [x1, y1, x2, y2],
                                    'name': name,
                                    'dist': round(dist, 1)
                                })

            tracked_map = tracker.update(detections)
            
            # --- DECISION LOGIC ---
            global_closest = 99.0
            urgent_warning = ""
            
            center_x = width // 2
            blocked_left = False
            blocked_center = False
            blocked_right = False
            
            # Process Tracked Objects
            for obj_id, obj in tracked_map.items():
                data = obj['data']
                dist = data['dist']
                name = data['name']
                x1, y1, x2, y2 = obj['box']
                cx = (x1 + x2) // 2
                
                if dist < global_closest: global_closest = dist
                
                # Danger Zone Logic
                safe_zone = int(width * 0.35) 
                z_left = center_x - (safe_zone // 2)
                z_right = center_x + (safe_zone // 2)

                if dist < 3.5:
                    if cx < z_left: blocked_left = True
                    elif cx > z_right: blocked_right = True
                    else:
                        blocked_center = True
                        # IMMEDIATE DANGER
                        if dist < 1.5:
                            urgent_warning = f"Stop! {name} Close!"
                        elif data['velocity'] > 0.3:
                            urgent_warning = f"Stop! {name} Approaching!"

                # Draw HUD
                color = (0, 255, 0)
                if dist < 2.0: color = (0, 165, 255) # Orange
                if dist < 1.2: color = (0, 0, 255)   # Red
                draw_hud(frame, x1, y1, x2, y2, color, f"{name} {dist}m")

            # --- VOICE LOGIC ---
            if urgent_warning:
                voice.say(urgent_warning, priority=0)
            elif blocked_center:
                if not blocked_left: voice.say("Veer Left", priority=1)
                elif not blocked_right: voice.say("Veer Right", priority=1)
                else: voice.say("Path Blocked", priority=1)
            
            # --- TERMINAL OUTPUT (SLOWED DOWN) ---
            if time.time() - last_print_time > 1.5: # Update terminal every 1.5s
                if global_closest < 99.0:
                    print(f"👀 Tracking: Closest Object at {global_closest}m", flush=True)
                last_print_time = time.time()

            # --- DISPLAY ---
            cv2.rectangle(frame, (0, height-30), (width, height), (0,0,0), -1)
            cv2.putText(frame, f"STATUS: ACTIVE | DIST: {global_closest}m", (10, height-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow('V.E.D.A. HUD', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

    except Exception as e:
        print(f"❌ Main Loop Error: {e}", flush=True)
    finally:
        voice.stop()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    start_veda()