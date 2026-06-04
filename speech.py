import threading
import time
import asyncio
import edge_tts
import os
import speech_recognition as sr
import pygame
import config
import ctypes
import whisper  # 🔥 ADD WHISPER

# 🔥 ALSA ERROR SUPPRESSION MAGIC 🔥
# This forces the Linux audio drivers to shut the hell up.
try:
    ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
    def py_error_handler(filename, line, function, err, fmt):
        pass # Do absolutely nothing with the error
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = ctypes.cdll.LoadLibrary('libasound.so.2')
    asound.snd_lib_error_set_handler(c_error_handler)
except OSError:
    pass

class SpeechSystem:
    """Handles fast Text-to-Speech (Edge-TTS) and Speech Recognition (Whisper AI)"""
    
    def __init__(self, on_user_input_callback):
        self.is_talking = False
        self.is_thinking = False 
        self.conversation_active = False
        self.last_speech_time = time.time()
        self.on_user_input = on_user_input_callback
        self.status_callback = None
        
        # Audio playback init
        pygame.mixer.init()
        
        # STT Setup
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.5 
        
        print("⏳ Loading Whisper AI (base.en)... This might take a few seconds.")
        # 🔥 Load the English-only base model 
        self.stt_model = whisper.load_model("base.en")
        print("✅ Whisper AI Loaded!")
        
        try:
            with sr.Microphone() as source:
                print("✅ Microphone found and ready!")
        except Exception as e:
            print(f"⚠️ No microphone: {e}")

    def set_status_callback(self, callback):
        self.status_callback = callback

    def set_status(self, text):
        if self.status_callback:
            self.status_callback(text)
        
    def speak(self, text):
        """Threaded TTS so it doesn't freeze the UI"""
        if not text: 
            return
        
        self.is_talking = True 
        threading.Thread(target=self._generate_and_play, args=(text,), daemon=True).start()

    def _generate_and_play(self, text):
        self.is_talking = True
        # Clean text for Ursina/Terminal (Removes Emojis)
        clean_text = "".join(c for c in text if c.isascii())
        self.set_status(f"HOLO: {clean_text[:50]}...")

        # Use a temporary file with a unique name to avoid ALSA locks
        temp_filename = f"speech_{int(time.time())}.mp3"
        
        try:
            # Generate the file
            communicate = edge_tts.Communicate(text, config.VOICE)
            asyncio.run(communicate.save(temp_filename))
            
            # Play via Pygame
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload() # Release the file
        except Exception as e:
            print(f"🚨 TTS Playback Error: {e}")
        finally:
            time.sleep(0.5)
            self.is_talking = False
            if os.path.exists(temp_filename):
                try: os.remove(temp_filename)
                except: pass

    def start_conversation(self):
        if self.conversation_active: 
            return
        self.conversation_active = True
        self.set_status("🗣️ Speak now...")
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        while self.conversation_active:
            # 1. Skip if busy (Check this BEFORE opening the mic)
            if self.is_talking or self.is_thinking or pygame.mixer.music.get_busy():
                time.sleep(0.1)
                continue
            
            # 2. Open the mic ONLY when she is done talking
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                
                try:
                    # Listen for a short burst
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=15)
                    
                    # 3. CRITICAL: Check if she started talking mid-sentence
                    if self.is_talking or self.is_thinking:
                        print("🗑️ Discarding stale audio (System became busy)")
                        continue
                    
                    print("🤖 Whisper is transcribing...")
                    
                    # 🔥 WHISPER TRANSCRIPTION LOGIC
                    temp_file = "temp_debug_audio.wav"
                    with open(temp_file, "wb") as f:
                        f.write(audio.get_wav_data())

                    # Transcribe using Whisper
                    result = self.stt_model.transcribe(temp_file, fp16=False)
                    text = result["text"].strip()
                    
                    # Cleanup
                    if os.path.exists(temp_file):
                        os.remove(temp_file)

                    if text:
                        print(f"✅ Whisper heard: {text}")
                        self.on_user_input(text)

                except (sr.WaitTimeoutError, sr.UnknownValueError):
                    continue
                except Exception as e:
                    print(f"🎤 Mic Error: {e}")

    def stop_conversation(self):
        self.conversation_active = False
        self.set_status("Waiting for visual wake-up or WAVE...") 
