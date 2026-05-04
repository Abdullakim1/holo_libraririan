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
        self.last_speech_time = 0
        self.on_user_input = on_user_input_callback
        self.status_callback = None
        
        # Speech recognizer (for commands after wake word)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
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
            self.set_status("Say 'wake up holo' or wave hand...")
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
        self.set_status("Say 'wake up holo' or wave hand...")
    
    def _continuous_listen(self):
        """Continuously listen during conversation - runs until timeout"""
        silence_timeout = config.CONVERSATION_TIMEOUT  # From config
        
        while self.conversation_active:
            # Wait if HOLO is talking
            if self.is_talking:
                self.last_speech_time = time.time()
                time.sleep(0.3)
                continue
            
            # Check for silence timeout
            if time.time() - self.last_speech_time > silence_timeout:
                print(f"⏰ {silence_timeout}s silence - ending conversation")
                self.stop_conversation()
                break
            
            # Try to hear user
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    
                    try:
                        audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=8)
                        user_text = None
                        
                        # Try Google first
                        try:
                            user_text = self.recognizer.recognize_google(audio)
                        except:
                            # Fallback to Sphinx
                            try:
                                user_text = self.recognizer.recognize_sphinx(audio)
                            except:
                                pass
                        
                        if user_text and len(user_text.strip()) > 1:
                            print(f"  🗣️: {user_text}")
                            self.set_status("You: " + user_text)
                            self.last_speech_time = time.time()
                            
                            # Check for exit phrases
                            if any(phrase in user_text.lower() for phrase in ['goodbye', 'bye', 'thanks', 'thank you', 'that is all', 'stop']):
                                print("👋 Exit phrase detected")
                                self.stop_conversation()
                                continue
                            
                            self.on_user_input(user_text)
                        else:
                            time.sleep(0.3)
                    
                    except sr.WaitTimeoutError:
                        # Natural pause - just continue
                        time.sleep(0.3)
                    
            except Exception as e:
                print(f"Listen error: {e}")
                time.sleep(1)
        
        print("💤 Conversation ended")
    
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
                    
                    subprocess.run(
                        ['mpv', '--no-video', '--really-quiet', tmp_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    os.unlink(tmp_path)
                except Exception as e:
                    print(f"TTS Error: {e}")
                
                self.is_talking = False
                
                # Update status based on state
                if self.conversation_active:
                    self.set_status("🗣️ Speak now...")
                else:
                    self.set_status("Say 'wake up holo' or wave hand...")
            
            asyncio.run(run_tts())
        
        threading.Thread(target=_tts, daemon=True).start() 
