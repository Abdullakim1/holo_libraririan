import json, os, sys, time, pandas as pd
import pyttsx3
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

# ========== CONFIG ==========
HOLO_AVATAR = """
   ╭─────────────╮
   │  ✦ HOLO ✦  │
   ╰─────────────╯
      ◈◈◈◈◈◈◈
"""

# ========== TTS ==========
tts = pyttsx3.init()
tts.setProperty("rate", 150)
tts.setProperty("volume", 1.0)

def speak(text: str):
    print(f"\n{HOLO_AVATAR}🔊 {text}\n")
    for c in text: sys.stdout.write(c); sys.stdout.flush(); time.sleep(0.02)
    print()
    tts.say(text); tts.runAndWait()

# ========== DATA ==========
df = pd.read_csv("library_data.csv")

def search_books(query: str) -> str:
    """Simple keyword search"""
    matches = df[df["Title"].str.contains(query, case=False, na=False)]
    if matches.empty: return "I couldn't find any books matching that."
    return matches[["Title", "Author", "Status"]].to_string(index=False)

def checkout(title: str) -> str:
    """Check out a book by exact title"""
    idx = df[df["Title"].str.lower() == title.lower()]
    if idx.empty: return f"'{title}' isn't in our catalog."
    if idx["Status"].iloc[0] == "Out": return f"'{title}' is already checked out."
    df.loc[idx.index[0], "Status"] = "Out"
    df.to_csv("library_data.csv", index=False)
    return f"✅ '{title}' has been checked out for you."

# ========== SIMPLE LLM PROMPT (no ReAct) ==========
prompt = PromptTemplate.from_template("""You are HOLO, a friendly library hologram.

Available books:
{books}

You can:
1. Search for books by title keyword
2. Check out a book by exact title

User: {input}
HOLO:""")

llm = ChatOllama(model="llama3.2", temperature=0.2)

def ask_holo(question: str) -> str:
    # First try direct LLM answer with book context
    books_ctx = df[["Title", "Author", "Status"]].head(10).to_string(index=False)
    full_prompt = prompt.format(books=books_ctx, input=question)
    
    try:
        response = llm.invoke(full_prompt).content.strip()
        # If LLM mentions checking out, actually do it
        if "check out" in response.lower() or "checked out" in response.lower():
            for title in df["Title"]:
                if title.lower() in question.lower():
                    result = checkout(title)
                    if "✅" in result: return result
        return response
    except:
        # Fallback: just search
        return search_books(question)

# ========== TEST MODE (NO MIC) ==========
if __name__ == "__main__":
    tests = [
        "What books do you have?",
        "Is Dune available?",
        "Check out Pride and Prejudice for me.",
        "Do you have any sci-fi books?"
    ]
    
    speak("Hello! I'm HOLO. Running voice test now.")
    
    for q in tests:
        print(f"\n🗣️ You: {q}")
        ans = ask_holo(q)
        print(f"🤖 HOLO: {ans}\n")
        speak(ans)
        time.sleep(1)
    
    speak("Test complete! I'm ready when you are.")
