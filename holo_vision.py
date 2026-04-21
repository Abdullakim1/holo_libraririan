import random
import json
import os
import sys
import time
import threading
import queue
from vosk import Model, KaldiRecognizer
import pyaudio
import pyttsx3
from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
import pandas as pd

# ========== CONFIG ==========
VOSK_MODEL_PATH = os.path.expanduser(".vosk/vosk-model")
AUDIO_CHUNK = 4000
SAMPLE_RATE = 16000
HOLO_AVATAR = """
   ╭─────────────╮
   │  ✦ HOLO ✦  │
   ╰─────────────╯
      ◈◈◈◈◈◈◈
"""

# ========== TTS ENGINE ==========
import tkinter as tk
import time
import math
# ========== HOLOGRAM GUI (Black Screen + Mouth Mimic) ==========
from PIL import Image, ImageDraw, ImageTk
import random
class HoloGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#000000')
        self.root.bind('<Escape>', lambda e: self.close())
        self.root.bind('q', lambda e: self.close())

        self.canvas = tk.Canvas(self.root, bg='#000000', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.cx, self.cy = w // 2, h // 2

        # LIBRARY BOOKSHELVES (left & right)
        for side in [-1, 1]:
            base_x = self.cx + (side * 450)
            # Main shelf
            self.canvas.create_rectangle(base_x-75, self.cy-250, base_x+75, self.cy+250,
                                        fill='#001122', outline='#004488', width=2)
            # Shelf lines (books)
            for shelf_y in range(-200, 250, 50):
                self.canvas.create_line(base_x-65, shelf_y+self.cy, base_x+65, shelf_y+self.cy,
                                       fill='#003366', width=1)

        # UPPER HOLOGRAM RING (large, glowing)
        self.upper_ring = self.canvas.create_oval(
            self.cx-220, self.cy-320, self.cx+220, self.cy-220,
            outline='#00d4ff', width=4
        )
        self.upper_ring_inner = self.canvas.create_oval(
            self.cx-200, self.cy-310, self.cx+200, self.cy-230,
            outline='#0088ff', width=2
        )

        # === PROFESSIONAL LIBRARIAN FIGURE ===
        
        # Head (oval, professional)
        self.head = self.canvas.create_oval(
            self.cx-28, self.cy-180, self.cx+28, self.cy-125,
            outline='#00ffff', width=2, fill='#001a33'
        )
        
        # Hair (styled bun)
        self.hair = self.canvas.create_oval(
            self.cx-25, self.cy-185, self.cx+25, self.cy-155,
            outline='#0088ff', width=1, fill='#002244'
        )

        # Glasses (professional look)
        self.glasses_l = self.canvas.create_oval(
            self.cx-18, self.cy-160, self.cx-6, self.cy-150,
            outline='#00ffff', width=2
        )
        self.glasses_r = self.canvas.create_oval(
            self.cx+6, self.cy-160, self.cx+18, self.cy-150,
            outline='#00ffff', width=2
        )
        self.glasses_bridge = self.canvas.create_line(
            self.cx-6, self.cy-155, self.cx+6, self.cy-155,
            fill='#00ffff', width=1
        )

        # Body (elegant dress/coat - professional librarian)
        self.body = self.canvas.create_polygon(
            self.cx-32, self.cy-125,   # shoulders left
            self.cx+32, self.cy-125,   # shoulders right
            self.cx+28, self.cy-20,    # waist right
            self.cx+35, self.cy+140,   # dress bottom right
            self.cx-35, self.cy+140,   # dress bottom left
            self.cx-28, self.cy-20,    # waist left
            fill='', outline='#00d4ff', width=3
        )
        
        # Body inner detail
        self.body_inner = self.canvas.create_polygon(
            self.cx-25, self.cy-115,
            self.cx+25, self.cy-115,
            self.cx+22, self.cy-10,
            self.cx+28, self.cy+130,
            self.cx-28, self.cy+130,
            self.cx-22, self.cy-10,
            fill='#001122', outline='#0066aa', width=1
        )

        # Left arm (holding a book/tablet gesture)
        self.arm_l = self.canvas.create_line(
            self.cx-28, self.cy-115,
            self.cx-55, self.cy-40,
            self.cx-50, self.cy+10,
            fill='#00d4ff', width=3, smooth=True
        )
        
        # Right arm (resting on desk gesture)
        self.arm_r = self.canvas.create_line(
            self.cx+28, self.cy-115,
            self.cx+55, self.cy-40,
            self.cx+48, self.cy+20,
            fill='#00d4ff', width=3, smooth=True
        )

        # Hands
        self.hand_l = self.canvas.create_oval(
            self.cx-53, self.cy+5, self.cx-47, self.cy+15,
            fill='#00ffff', outline=''
        )
        self.hand_r = self.canvas.create_oval(
            self.cx+45, self.cy+15, self.cx+51, self.cy+25,
            fill='#00ffff', outline=''
        )

        # Book/tablet in hand
        self.book = self.canvas.create_rectangle(
            self.cx-58, self.cy-5, self.cx-42, self.cy+12,
            outline='#00ffff', width=1, fill='#002244'
        )

        # LOWER PLATFORM RING
        self.platform = self.canvas.create_oval(
            self.cx-180, self.cy+160, self.cx+180, self.cy+200,
            outline='#00d4ff', width=3, dash=(12, 6)
        )
        self.platform_inner = self.canvas.create_oval(
            self.cx-160, self.cy+170, self.cx+160, self.cy+190,
            outline='#0088ff', width=1
        )

        self.is_talking = False

        # TTS
        self.tts = pyttsx3.init()
        self.tts.setProperty('rate', 145)
        self.tts.setProperty('volume', 0.9)

        self._animate()
        self.root.mainloop()

    def _animate(self):
        t = time.time()
        
        # Gentle floating
        float_y = math.sin(t * 1.8) * 6
        
        # Animate all parts
        self.canvas.move(self.upper_ring, 0, float_y * 0.5)
        self.canvas.move(self.upper_ring_inner, 0, float_y * 0.5)
        self.canvas.move(self.head, 0, float_y)
        self.canvas.move(self.hair, 0, float_y)
        self.canvas.move(self.glasses_l, 0, float_y)
        self.canvas.move(self.glasses_r, 0, float_y)
        self.canvas.move(self.glasses_bridge, 0, float_y)
        self.canvas.move(self.body, 0, float_y)
        self.canvas.move(self.body_inner, 0, float_y)
        self.canvas.move(self.arm_l, 0, float_y)
        self.canvas.move(self.arm_r, 0, float_y)
        self.canvas.move(self.hand_l, 0, float_y)
        self.canvas.move(self.hand_r, 0, float_y)
        self.canvas.move(self.book, 0, float_y)
        self.canvas.move(self.platform, 0, float_y * 0.3)
        self.canvas.move(self.platform_inner, 0, float_y * 0.3)

        # Talking animation - pulse and glow
        if self.is_talking:
            glow = 4 + abs(math.sin(t * 12)) * 2
            self.canvas.itemconfig(self.upper_ring, width=glow)
            self.canvas.itemconfig(self.body, width=glow)
            self.canvas.itemconfig(self.head, width=glow+1)
        else:
            self.canvas.itemconfig(self.upper_ring, width=4)
            self.canvas.itemconfig(self.body, width=3)
            self.canvas.itemconfig(self.head, width=2)

        self._anim_id = self.root.after(50, self._animate)

    def speak(self, text: str):
        self.is_talking = True
        def _do_tts():
            self.tts.say(text)
            self.tts.runAndWait()
            self.root.after(0, lambda: setattr(self, 'is_talking', False))
        threading.Thread(target=_do_tts, daemon=True).start()

    def close(self):
        self.root.destroy()
        # ========== RUN ==========
if __name__ == "__main__":
    print("🌀 Starting HOLO hologram... (Press ESC or 'q' to exit)")
    
    # Initialize GUI (this starts the tkinter mainloop)
    holo = HoloGUI()
    
    # Test queries to speak
    tests = [
        "Hello! I am HOLO, your library assistant.",
        "I have Dune, Pride and Prejudice, and more.",
        "Ask me about any book, or say goodbye to exit."
    ]
    
    # Run tests in background thread so GUI stays responsive
    def run_tests():
        time.sleep(1.5)  # Wait for GUI to fully render
        for msg in tests:
            holo.speak(msg)
            time.sleep(3)  # Pause between messages
        # Keep window open after tests
        print("✅ Tests complete. Window will stay open. Press ESC to exit.")
    
    threading.Thread(target=run_tests, daemon=True).start()
