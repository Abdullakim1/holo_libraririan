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
        self.wake_word_active = True
        self.on_user_input = on_user_input_callback
        self.status_callback = None
        
        # Speech recognizer (for commands after wake word)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0
        
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
            self.vosk_recognizer.SetWords(True)  # Enable word timing
            self.audio_queue = queue.Queue()
            self.wake_word = config.WAKE_WORD.lower()
            print(f"✅ Listening for wake word: '{self.wake_word}' (Offline Vosk)")
            self.set_status(f"Say '{self.wake_word}'...")
        except Exception as e:
            print(f"⚠️ Wake word disabled: {e}")
            self.vosk_model = None
            self.set_status("Press SPACE to talk or T to type")
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback for sounddevice audio stream"""
        if status:
            print(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def _wake_word_loop(self):
        """Continuously listen for wake word using Vosk"""
        try:
            with sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                device=None,
                dtype='int16',
                channels=1,
                callback=self._audio_callback
            ):
                print(f"🎤 Microphone active - speak now...")
                
                while self.wake_word_active:
                    audio_data = self.audio_queue.get()
                    
                    if self.vosk_recognizer.AcceptWaveform(audio_data):
                        result = json.loads(self.vosk_recognizer.Result())
                        text = result.get('text', '').lower()
                        
                        # DEBUG: Print everything Vosk hears
                        if text and len(text) > 1:
                            print(f"  Heard: '{text}'")
                        
                        # Check for individual words too
                        words = text.split()
                        wake_parts = self.wake_word.split()
                        
                        # Match full wake word OR individual words
                        if self.wake_word in text or any(word in words for word in wake_parts if len(word) > 2):
                            print(f"🎯 WAKE WORD DETECTED! Full text: '{text}'")
                            
                            if not self.is_talking and not self.is_listening:
                                self.set_status("Wake word detected! Listening...")
                                self.listen()
                    
                    # Check partial results for faster deection
                    else:
                        partial = json.loads(self.vosk_recognizer.PartialResult())
                        text = partial.get('partial', '').lower()
                        
                        # DEBUG: Show partial results
                        if text and len(text) > 1:
                            print(f"  Partial: '{text}'")
                        
                        if self.wake_word in text:
                            print(f"⚡ WAKE WORD in partial! '{text}'")
                            
                            if not self.is_talking and not self.is_listening:
                                self.set_status("Wake word detected! Listening...")
                                self.listen()
                                
        except Exception as e:
            print(f"Wake word loop error: {e}")
            import traceback
            traceback.print_exc()
            self.set_status("Wake word error. Press SPACE to talk.")
    
    def set_status_callback(self, callback):
        self.status_callback = callback
    
    def set_status(self, text):
        if self.status_callback:
            self.status_callback(text)
        else:
            print(f"Status: {text}")
    
    def speak(self, text):
        """Speak text using Edge TTS"""
        self.is_talking = True
        self.set_status("HOLO: " + text[:80] + "...")
        
        def _tts():
            async def run_tts():
                try:
                    communicate = edge_tts.Communicate(text, config.VOICE)
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                        tmp_path = tmp.name
                    await communicate.save(tmp_path)
                    
                    subprocess.run(['mpv', '--no-video', '--really-quiet', tmp_path],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.unlink(tmp_path)
                except Exception as e:
                    print(f"TTS Error: {e}")
                
                self.is_talking = False
                self.set_status(f"Say '{self.wake_word}'...")
            
            asyncio.run(run_tts())
        
        threading.Thread(target=_tts, daemon=True).start()
    
    def listen(self):
        """Listen for user speech after wake word"""
        if self.is_listening or self.is_talking:
            return
        
        if self.microphone is None:
            self.set_status("No microphone! Press T to type.")
            return
        
        self.is_listening = True
        self.set_status("🎤 Listening...")
        
        def _listen():
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    self.set_status("💭 Thinking...")
                    
                    user_text = None
                    try:
                        user_text = self.recognizer.recognize_google(audio)
                        print(f"  Heard: {user_text}")
                    except:
                        try:
                            user_text = self.recognizer.recognize_sphinx(audio)
                            print(f"  Sphinx heard: {user_text}")
                        except:
                            pass
                    
                    if not user_text:
                        self.set_status("Couldn't understand. Please try again.")
                        time.sleep(2)
                        self.set_status(f"Say '{self.wake_word}'...")
                        self.is_listening = False
                        return
                    
                    self.set_status("You: " + user_text)
                    self.on_user_input(user_text)
                    
            except sr.WaitTimeoutError:
                self.set_status("No speech detected. Try again.")
                time.sleep(2)
                self.set_status(f"Say '{self.wake_word}'...")
            except Exception as e:
                print(f"Listen error: {e}")
                self.set_status("Error. Please try again.")
                time.sleep(2)
                self.set_status(f"Say '{self.wake_word}'...")
            
            self.is_listening = False
        
        threading.Thread(target=_listen, daemon=True).start()
