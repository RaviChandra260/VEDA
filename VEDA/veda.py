print("--- I AM THE NEW CODE ---") # PROOF THAT FILE IS UPDATED
import sys
import os
import threading
import time

# --- IMPORT MODULES ---
import veda_nav
import currency_scan

# Safe Import for Reader
try:
    import text_reader
except ImportError:
    pass 

def speak(text):
    def _run():
        try:
            os.system(f'mshta vbscript:Execute("CreateObject(""SAPI.SpVoice"").Speak(""{text}"")(window.close)")')
        except: pass
    threading.Thread(target=_run).start()

def get_camera_choice():
    print("\n--- Select Camera Input ---")
    print(" [1] WiFi Camera (DroidCam)")
    print(" [2] USB / Laptop Webcam")
    choice = input("Enter Choice (1 or 2): ").strip()
    return "usb" if choice == '2' else "wifi"

def main_menu():
    speak("System Online")
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n=======================================")
        print("      V.E.D.A.  ULTIMATE SYSTEM      ")
        print("=======================================")
        print(" [1]  Navigation Mode")
        print(" [2]  Currency Mode")
        print(" [3]  Text Reader Mode")
        print(" [4]  EXIT")
        print("=======================================")
        
        # --- DEBUGGING STEP ---
        raw_input = input("Enter Choice (1-4): ")
        choice = raw_input.strip() # Removes spaces
        
        # THIS WILL PRINT EXACTLY WHAT THE COMPUTER SEES
        print(f"DEBUG INFO: You typed '{raw_input}' -> Cleaned: '{choice}'")

        if choice == '1':
            cam_mode = get_camera_choice()
            try: veda_nav.start_veda(cam_mode)
            except Exception as e: print(e); input("Error. Press Enter...")
                
        elif choice == '2':
            cam_mode = get_camera_choice()
            try: currency_scan.start_currency(cam_mode)
            except Exception as e: print(e); input("Error. Press Enter...")
        
        elif choice == '3':
            print(">> ATTEMPTING TO LOAD TEXT READER...")
            if 'text_reader' not in sys.modules:
                print("❌ Error: text_reader.py NOT FOUND.")
                print("Make sure the file is named 'text_reader.py' (not main.py)")
                input("Press Enter to fix...")
                continue
                
            cam_mode = get_camera_choice()
            try:
                # Force reload in case you changed the file
                import importlib
                importlib.reload(text_reader)
                text_reader.start_reader(cam_mode)
            except Exception as e:
                print(f"❌ CRASH: {e}")
                input("Press Enter...")
                
        elif choice == '4':
            sys.exit()
        
        else:
            print(f"❌ INVALID: The computer did not accept '{choice}'")
            print("Please type exactly 1, 2, 3, or 4")
            time.sleep(3)

if __name__ == "__main__":
    main_menu()