import tkinter as tk
from PIL import Image, ImageTk, ImageFilter, ImageEnhance
import pyttsx3
import threading
import time
import os

# ========== CONFIG ==========
HOLO_IMAGE_PATH = "holo_librarian.webp"  # ← Put your PNG here
BG_COLOR = "#000000"
GLOW_COLOR = "#00d4ff"

# ========== TTS ==========
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

class HoloImageGUI:
    def __init__(self, image_path):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg=BG_COLOR)
        self.root.bind('<Escape>', lambda e: self.close())
        self.root.bind('q', lambda e: self.close())

        self.canvas = tk.Canvas(self.root, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.cx, self.cy = w // 2, h // 2

        # Load and prepare image
        self.original_img = self._load_image(image_path, height=500)
        self.glow_img = self._add_glow(self.original_img)
        
        # Display image
        self.img_item = self.canvas.create_image(self.cx, self.cy, image=self.glow_img, anchor='center')
        
        # Floating animation state
        self.float_offset = 0
        self.is_talking = False

        # Start animation
        self._animate()
        self.root.mainloop()

    def _load_image(self, path, height=500):
        """Load PNG, resize, make compatible with Tkinter"""
        try:
            img = Image.open(path).convert("RGBA")
            # Resize while keeping aspect ratio
            ratio = height / img.height
            new_size = (int(img.width * ratio), height)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"⚠️ Could not load image: {e}")
            # Fallback: colored rectangle
            fallback = Image.new("RGBA", (200, 400), (0, 212, 255, 180))
            return ImageTk.PhotoImage(fallback)

    def _add_glow(self, img_tk):
        """Add cyan glow effect around image"""
        # Convert back to PIL for processing
        # (simplified: just return the image for now)
        return img_tk

    def _animate(self):
        """Smooth floating animation"""
        t = time.time()
        self.float_offset = math.sin(t * 2) * 8
        
        # Move image up/down
        self.canvas.coords(self.img_item, self.cx, self.cy + self.float_offset)
        
        # Pulse glow when talking
        if self.is_talking:
            alpha = 200 + int(abs(math.sin(t * 10)) * 55)
            # Note: Full glow animation requires more PIL processing
            # This is a simplified version
        
        self.root.after(50, self._animate)

    def speak(self, text: str):
        """Trigger TTS + talking animation"""
        self.is_talking = True
        def _do_tts():
            tts.say(text)
            tts.runAndWait()
            time.sleep(0.3)
            self.is_talking = False
        threading.Thread(target=_do_tts, daemon=True).start()

    def close(self):
        self.root.destroy()

# ========== AGENT LOGIC (same as before) ==========
import pandas as pd
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

df = pd.read_csv("library_data.csv")

def search_books(query: str) -> str:
    matches = df[df["Title"].str.contains(query, case=False, na=False)]
    return matches[["Title", "Author", "Status"]].to_string(index=False) if not matches.empty else "I couldn't find that."

def checkout(title: str) -> str:
    idx = df[df["Title"].str.lower() == title.lower()]
    if idx.empty: return f"'{title}' isn't in our catalog."
    if idx["Status"].iloc[0] == "Out": return f"'{title}' is already checked out."
    df.loc[idx.index[0], "Status"] = "Out"
    df.to_csv("library_data.csv", index=False)
    return f"✅ '{title}' has been checked out for you."

llm = ChatOllama(model="llama3.2", temperature=0.2)
prompt = PromptTemplate.from_template("""You are HOLO, a friendly library hologram.
Available books:
{books}
User: {input}
HOLO:""")

def ask_holo(question: str) -> str:
    books_ctx = df[["Title", "Author", "Status"]].head(10).to_string(index=False)
    full = prompt.format(books=books_ctx, input=question)
    try:
        resp = llm.invoke(full).content.strip()
        if "check out" in resp.lower():
            for t in df["Title"]:
                if t.lower() in question.lower():
                    res = checkout(t)
                    if "✅" in res: return res
        return resp
    except: return "I'm having trouble processing that."

# ========== RUN ==========
if __name__ == "__main__":
    import math  # Needed for animation
    
    # Start GUI in main thread
    holo = HoloImageGUI(HOLO_IMAGE_PATH)
    
    # Run test queries in background
    def run_tests():
        time.sleep(2)
        tests = [
            "Hello! I am HOLO, your hologram librarian.",
            "I can help you find books, check availability, or check out titles.",
            "What book would you like to explore today?"
        ]
        for msg in tests:
            holo.speak(msg)
            time.sleep(4)
    
    threading.Thread(target=run_tests, daemon=True).start()
