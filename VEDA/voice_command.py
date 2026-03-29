import speech_recognition as sr
import os
import sys
import veda_nav
import currency_scan

# --- VOICE FEEDBACK FUNCTION ---
def speak_feedback(text):
    """
    Uses Windows SAPI to speak system status updates.
    """
    print(f"System: {text}")
    # Using mshta to run VBScript on the fly for system voice
    os.system(f'mshta vbscript:Execute("CreateObject(""SAPI.SpVoice"").Speak(""{text}"")(window.close)")')

# --- LISTENER FUNCTION ---
def listen_command():
    """
    Listens for a voice command and converts it to text.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n[LISTENING] Waiting for command...")
        # Adjust for background noise to improve accuracy
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            # Listen with a timeout to prevent hanging
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            command = recognizer.recognize_google(audio).lower()
            print(f"[USER] said: {command}")
            return command
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            print("Network error with Speech Recognition service.")
            return ""

# --- MAIN LOOP ---
def main():
    speak_feedback("System Online. Waiting for voice commands.")
    
    while True:
        command = listen_command()

        # CONDITION 1: NAVIGATION MODE
        if "navigation" in command or "object" in command or "activate navigation" in command:
            speak_feedback("Activating Navigation Mode")
            try:
                veda_nav.start_veda()
            except Exception as e:
                print(f"Error starting Navigation: {e}")
            speak_feedback("Returning to voice menu")

        # CONDITION 2: CURRENCY MODE
        elif "currency" in command or "money" in command or "activate currency" in command:
            speak_feedback("Activating Currency Detection")
            try:
                currency_scan.start_currency()
            except Exception as e:
                print(f"Error starting Currency: {e}")
            speak_feedback("Returning to voice menu")

        # CONDITION 3: TERMINATE SYSTEM
        elif "terminate" in command or "exit" in command:
            speak_feedback("Shutting down system")
            sys.exit()

if __name__ == "__main__":
    main()