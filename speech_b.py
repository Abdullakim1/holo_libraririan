import threading
import time
import asyncio
import edge_tts
import subprocess
import tempfile
import os
import speech_recognition as sr
import vosk
import sounddevice as sd
import numpy as np
import queue
import json
import config

class SpeechSystem:
    """Handles text-to-speech, speech recognition, and wake word detection"""
    
    def __init__(self, on_user_input_callback):
        self.is_talking = False
        self.is_listening = False
        self.conversation_active = False
        self.wake_word_active = True  # <--- ADD THIS LINE HERE
        self.last_speech_time = 0
        self.on_user_input = on_user_input_callback
        self.status_callback = None
        
        # Speech recognizer (for commands after wake word)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 2
        
        # Microphone check
        try:
            self.microphone = sr.Microphone()
            print("✅ Microphone found!")
        except Exception as e:
            print(f"⚠️ No microphone: {e}")
            self.microphone = None
        
        # Vosk wake word setup
        self._init_vosk_wake_word()
        
        # Start wake word listener
        if self.vosk_model:
            self.wake_thread = threading.Thread(target=self._wake_word_loop, daemon=True)
            self.wake_thread.start()
    
    def _init_vosk_wake_word(self):
        """Initialize Vosk for wake word detection"""
        try:
            self.vosk_model = vosk.Model(config.VOSK_MODEL_PATH)
            self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000)
            self.vosk_recognizer.SetWords(True)
            self.audio_queue = queue.Queue()
            self.wake_word = config.WAKE_WORD.lower()
            print(f"✅ Vosk ready! Wake word: '{self.wake_word}'")
            self.set_status("Say 'wake up' or wave hand...")
        except Exception as e:
            print(f"⚠️ Vosk disabled: {e}")
            self.vosk_model = None
            self.set_status("Press SPACE to talk or T to type")
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for sounddevice audio stream"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def _wake_word_loop(self):
        """Listen for wake word using Vosk in background"""
        try:
            with sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                device=None,
                dtype='int16',
                channels=1,
                callback=self._audio_callback
            ):
                print(f"🎤 Wake word listener active...")
                
                while self.wake_word_active:
                    audio_data = self.audio_queue.get()
                    
                    if self.vosk_recognizer.AcceptWaveform(audio_data):
                        result = json.loads(self.vosk_recognizer.Result())
                        text = result.get('text', '').lower()
                        
                        # Only respond to wake word when not in conversation
                        if text and not self.conversation_active and not self.is_talking:
                            if self.wake_word in text:
                                print(f"🎯 Wake word: '{text}'")
                                self.start_conversation()
                    
                    # Partial results for faster detection
                    else:
                        partial = json.loads(self.vosk_recognizer.PartialResult())
                        text = partial.get('partial', '').lower()
                        if text:
                            print(f"Vosk hearing: '{text}'")
                        
                        if self.wake_word in text and not self.conversation_active and not self.is_talking:
                            print(f"⚡ Wake word detected!")
                            self.start_conversation()
                                
        except Exception as e:
            print(f"Wake word error: {e}")
   
    def start_conversation(self):
        """Start continuous conversation mode - called by wake word, wave, or SPACE"""
        if self.conversation_active:
            return  # Already in conversation
        
        self.conversation_active = True
        self.last_speech_time = time.time()
        print("🗣️ Conversation mode ON - speak freely!")
        self.set_status("🗣️ Listening... speak now!")
        
        # Start continuous listening in background
        conv_thread = threading.Thread(target=self._continuous_listen, daemon=True)
        conv_thread.start()
    
    def stop_conversation(self):
        """End conversation mode"""
        self.conversation_active = False
        print("💤 Conversation mode OFF")
        self.set_status("Say 'wake up' or wave hand...")
    def _process_and_respond(self, audio):
        """Helper to process voice and trigger AI without blocking the mic"""
        try:
            # Try Google (Fastest)
            user_text = self.recognizer.recognize_google(audio)
            
            if user_text and len(user_text.strip()) > 1:
                print(f"  🗣️: {user_text}")
                self.set_status("You: " + user_text)
                
                # Check for exit
                exit_phrases = ['goodbye', 'bye', 'stop', 'go to sleep', 'thank you that is all']
                if any(phrase in user_text.lower() for phrase in exit_phrases):
                    self.speak("Goodbye! I'll be here if you need me.")
                    self.stop_conversation()
                else:
                    # Send to AI
                    self.on_user_input(user_text)
        except sr.UnknownValueError:
            pass # Didn't understand, just ignore
        except Exception as e:
            print(f"Recognition error: {e}")
    def _continuous_listen(self):
        """Continuously listen during conversation - Refined for fluidity"""
        
        # 1. Calibrate ONCE before entering the loop
        with self.microphone as source:
            print("🎤 Calibrating microphone silence levels...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            self.recognizer.energy_threshold = 300 # Adjust this if she is too sensitive
            self.recognizer.dynamic_energy_threshold = True

        while self.conversation_active:
            # If she's talking, we wait, but we check more frequently (0.1s)
            if self.is_talking:
                time.sleep(0.1)
                continue
            
            try:
                with self.microphone as source:
                    # phrase_time_limit=None allows you to speak long sentences without being cut
                    # timeout=None means she waits forever until you speak
                    print("👂 Listening...")
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=None)
                    
                    # Process recognition in a separate thread so the listener stays "hot"
                    threading.Thread(target=self._process_and_respond, args=(audio,), daemon=True).start()
                    
            except Exception as e:
                print(f"Listen error: {e}")
                time.sleep(0.2)
    def set_status_callback(self, callback):
        """Set function to call for status updates"""
        self.status_callback = callback
    
    def set_status(self, text):
        """Update status text in UI"""
        if self.status_callback:
            self.status_callback(text)
    
    def speak(self, text):
        """Speak text using Edge TTS (natural female voice)"""
        self.is_talking = True
        self.last_speech_time = time.time()
        self.set_status("HOLO: " + text[:80] + "...")
        
        def _tts():
            async def run_tts():
                try:
                    communicate = edge_tts.Communicate(text, config.VOICE)
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                        tmp_path = tmp.name
                    await communicate.save(tmp_path)
                    player = subprocess.Popen(
                    ['mpv', '--no-video', '--really-quiet', tmp_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
    )
    
    # We set talking to True
                    self.is_talking = True
    
    # Wait for the player to actually finish before allowing the mic to open again
                    player.wait() 
    
                    os.unlink(tmp_path)
                    self.is_talking = False   
                except Exception as e:
                    print(f"TTS Error: {e}")
                
                self.is_talking = False
                
                # Update status based on state
                if self.conversation_active:
                    self.set_status("🗣️ Speak now...")
                else:
                    self.set_status("Say 'wake up' or wave hand...")
            
            asyncio.run(run_tts())
        
        threading.Thread(target=_tts, daemon=True).start() 
