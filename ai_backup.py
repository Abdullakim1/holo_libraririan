import requests
import config
import re
from database import LibraryDB

class HoloAI:
    def __init__(self):
        self.db = LibraryDB()
        self.conversation_history = []
        self.current_user_name = "Guest"
        self.current_user_id = "guest_01"

        # UPGRADED SYSTEM PROMPT
        
        self.system_prompt = """You are HOLO, a helpful hologram librarian. Be natural and helpful.

DATABASE COMMANDS:
- [SEARCH: exact book title] - Look up a book
- [CHECKOUT: exact book title] - Check out a book for registered users
- [REGISTER: Full Name] - Register a new user (use exact name they give)

RULES:
1: If someone asks to borrow and they're not registered:
  Ask: "What's your full name?"
  
2: After they give their name:
  Ask: "What's your library ID number?"
  
3: After they give ID:
  Ask: "Are you a student or faculty?"
  
4: After they answer:
  Use [REGISTER: Name, ID, Role]
5. When they confirm, use [CHECKOUT: Exact Book Title]
6. Keep responses short and friendly. No asterisks.

Current user: {name}"""

        self._test_connection()


    def _test_connection(self):
        try:
            requests.post(config.OLLAMA_URL, json={"model": config.OLLAMA_MODEL, "prompt": "Hi", "stream": False}, timeout=5)
            print("✅ Ollama connected to HOLO Brain!")
        except Exception:
            print("⚠️ Ollama not reachable.")

    def identify_user(self, name):
        self.current_user_name = name
        self.current_user_id = name.lower().replace(" ", "_")

    def get_response(self, user_input):
        """Get AI response and process database actions"""
        print(f"\n📝 User ({self.current_user_name}): {user_input}")
        
        # 🔥 Track pending book requests
        if not hasattr(self, 'pending_book'):
            self.pending_book = None
        
        prompt = f"{self.system_prompt}\n"
        for msg in self.conversation_history[-6:]:
            prompt += f"{msg['role']}: {msg['content']}\n"
        prompt += f"User: {user_input}\nHOLO:"
        
        try:
            response = requests.post(
                config.OLLAMA_URL,
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "stop": ["User:", "HOLO:"]}
                },
                timeout=60
            )
            
            if response.status_code == 200:
                ai_text = response.json().get('response', '').strip()
                
                # --- DATABASE INTERCEPTOR ---
                match = re.search(r'\[(SEARCH|CHECKOUT|RETURN|REGISTER):\s*(.*?)\]', ai_text)
                
                if match:
                    action = match.group(1)
                    params = match.group(2).strip()
                    
                    if action == "SEARCH":
                        print(f"⚙️ DB: SEARCH for '{params}'")
                        # Remember this book in case they want to borrow it
                        self.pending_book = params
                        db_msg = self.db.search_book(params)
                        
                    elif action == "CHECKOUT":
                        print(f"⚙️ DB: CHECKOUT '{params}' for {self.current_user_name}")
                        db_msg = self.db.checkout_book(
                            self.current_user_name, 
                            self.current_user_id, 
                            params
                        )
                        
                    elif action == "REGISTER":
                        parts = params.split(',')
                        name = parts[0].strip() if len(parts) > 0 else "Unknown"
                        user_id = parts[1].strip() if len(parts) > 1 else name.lower().replace(" ", "_")
                        role = parts[2].strip() if len(parts) > 2 else "member"
                        
                        print(f"⚙️ DB: REGISTER {name} (ID: {user_id}, Role: {role})")
                        result = self.db.get_or_create_user(user_id, name, role)
                        # Update identity
                        self.current_user_name = name
                        self.current_user_id = user_id
                        
                        db_msg = f"Registration complete! Welcome, {name}."
                        
                        # If there was a pending book, remind about it
                        if self.pending_book:
                            db_msg += f" Would you still like to borrow '{self.pending_book}'?"
                    
                    # Clean the tag from response
                    ai_text = re.sub(r'\[.*?\]', '', ai_text).strip()
                    if db_msg:
                        ai_text = db_msg + " " + ai_text
                
                ai_text = ai_text.replace('*', '').strip()
                self.conversation_history.append({"role": "User", "content": user_input})
                self.conversation_history.append({"role": "HOLO", "content": ai_text})
                
                print(f"🤖 HOLO: {ai_text}")
                return ai_text
                
            return "I am having trouble connecting to my memory."
        except Exception as e:
            return f"Error: {e}"
