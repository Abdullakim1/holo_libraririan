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
tts = pyttsx3.init()
tts.setProperty("rate", 160)
tts.setProperty("volume", 0.9)

def speak(text: str):
    """Speak aloud with typing effect + hologram header"""
    print(f"\n{HOLO_AVATAR}🔊 {text}\n")
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.02)  # typing speed
    print()
    tts.say(text)
    tts.runAndWait()

# ========== STT LISTENER ==========
def listen(timeout=8) -> str:
    """Listen for speech, return text. Press Ctrl+C to cancel."""
    model = Model(VOSK_MODEL_PATH)
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    p = pyaudio.PyAudio()
    
    print(f"{HOLO_AVATAR}🎤 Listening... (speak now, {timeout}s)")
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, frames_per_buffer=AUDIO_CHUNK)
    stream.start_stream()
    
    start = time.time()
    while time.time() - start < timeout:
        data = stream.read(AUDIO_CHUNK, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text","").strip()
            if "text":
                stream.stop_stream(); stream.close(); p.terminate()
                return text
    final = json.loads(recognizer.FinalResult())
    stream.stop_stream(); stream.close(); p.terminate()
    return final.get("text", "").strip()
    

# ========== YOUR EXISTING AGENT (unchanged logic) ==========
df = pd.read_csv("library_data.csv")

def search_library(query: str) -> str:
    results = df[df["Title"].str.contains(query, case=False, na=False)]
    if results.empty: return "No books found."
    return results[["Title", "Author", "Status"]].to_string(index=False)

def check_out_book(title: str) -> str:
    mask = df["Title"].str.lower() == title.lower()
    if not mask.any(): return f"'{title}' not found."
    if df.loc[mask, "Status"].iloc[0] == "Out": return f"'{title}' already checked out."
    df.loc[mask, "Status"] = "Out"
    df.to_csv("library_data.csv", index=False)
    return f"✅ '{title}' checked out."

tools = [
    Tool(name="SearchBooks", func=search_library, description="Search by title. Input: plain text."),
    Tool(name="CheckOut", func=check_out_book, description="Check out by exact title. Updates CSV.")
]

REACT_TEMPLATE = """You are HOLO, a friendly library hologram. Be concise, warm, and helpful.

TOOLS:
{tools}

FORMAT:
- Action: ONE of [{tool_names}]
- Action Input: PLAIN TEXT ONLY (no quotes, no parentheses)
- After Final Answer, output NOTHING else.

Question: {input}
Thought:{agent_scratchpad}"""

prompt = PromptTemplate.from_template(REACT_TEMPLATE)
llm = ChatOllama(model="llama3.2", temperature=0.3)
agent = create_react_agent(llm, tools, prompt)

# ⚠️ Added limits to prevent infinite loops on local models
executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True, 
    max_iterations=5, 
    max_execution_time=30
)

def ask_agent(question: str) -> str:
    try:
        result = executor.invoke({"input": question})
        return result.get("output", "I'm not sure. Try asking about a specific book.")
    except Exception as e:
        return f"Sorry, I hit a limit. ({str(e)[:40]})"

# ========== VOICE TEST MODE (No Mic Required) ==========
if __name__ == "__main__":
    test_queries = [
        "What books do you have?",
        "Is Dune available?",
        "Check out Pride and Prejudice for me."
    ]
    
    speak("Hello! I'm HOLO. Running voice test now.")
    
    for q in test_queries:
        print(f"\n🗣️ Query: {q}")
        response = ask_agent(q)
        print(f"🤖 Response: {response}\n")
        speak(response)
        time.sleep(1.5)  # Pause between responses
        
    speak("Test complete. I'm ready for your questions.")
