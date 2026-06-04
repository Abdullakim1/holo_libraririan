import requests
import config
import re
import json
from database import LibraryDB

class HoloAI:
    def __init__(self):
        self.db = LibraryDB()
        self.conversation_history = []
        self.current_user_name = "Guest"
        self.current_user_id = "guest_01"
        self.pending_book = None
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

    def _save_history(self, user_input, response):
        self.conversation_history.append({"role": "User", "content": user_input})
        self.conversation_history.append({"role": "HOLO", "content": response})

    def _classify_intent(self, user_input):
        """Ask Llama to classify the intent and extract parameters"""
        prompt = f"""You are an intent classifier for a library system.
Current user: {self.current_user_name} (ID: {self.current_user_id})

Output ONLY a JSON object: {{"intent": "INTENT", "params": {{...}}}}

INTENTS:

- "library_stats" - User asks how many books the LIBRARY has, total collection size, or library inventory
  Examples: "how many books do you have", "how big is the library", "total books in library"
  
- "who_am_i" - User asks about their OWN identity
  Examples: "who am i", "do you know me", "what's my name"

- "my_books" - User asks about THEIR OWN checked out books (uses words "my", "I", "me")
  Examples: "what books did I borrow", "my books", "what do I have checked out"

- "return_book" - User wants to return a book
  params: {{"title": "book title"}}

- "borrow_book" - User wants to borrow a book
  params: {{"title": "book title", "quantity": number}}

- "search_books" - User wants to find books by subject/topic
  params: {{"query": "single keyword"}}
  Examples: "books about biology" → query: "biology", "science books" → query: "science"

- "browse_books" - User wants to see what books the library has
  Examples: "what books do you have", "show me what's available"

- "register" - User wants to register
  params: {{"name": "full name"}}

- "chat" - Greetings, small talk, or anything else

CRITICAL: 
- "how many books do YOU have" → library_stats (asking about the library)
- "how many books do I have" → my_books (asking about their own checkouts)
- If unsure, use "chat". NEVER make up information about money, prices, or anything not in the system.

User: {user_input}
JSON:"""
        
        try:
            response = requests.post(
                config.OLLAMA_URL,
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0, "stop": ["\n\n"]}
                },
                timeout=15
            )
            if response.status_code == 200:
                text = response.json().get('response', '').strip()
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
        except:
            pass
        return {"intent": "chat", "params": {}}


        try:
            response = requests.post(
                config.OLLAMA_URL,
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "stop": ["\n\n"]}
                },
                timeout=15
            )
            if response.status_code == 200:
                text = response.json().get('response', '').strip()
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
        except:
            pass
        return {"intent": "chat", "params": {}}

    def _execute_intent(self, intent_data):
        """Execute the database action based on intent"""
        intent = intent_data.get("intent", "chat")
        params = intent_data.get("params", {})

        if intent == "who_am_i":
            if self.current_user_name not in ["Guest", "Unknown"]:
                return f"You're {self.current_user_name}, a registered library member!"
            return "I don't know you yet. Tell me your name to register!"

        elif intent == "my_books":
            self.db.cursor.execute(
                "SELECT book_title, checkout_date, due_date FROM checkouts WHERE user_id = %s AND status = 'active'",
                (self.current_user_id,)
            )
            checkouts = self.db.cursor.fetchall()
            if checkouts:
                parts = [f"'{t}' (due: {d})" for t, _, d in checkouts]
                return f"You have {len(checkouts)} book(s): " + "; ".join(parts) + "."
            return "You don't have any books checked out right now."

        elif intent == "return_book":
            title = params.get("title", "")
            if title:
                self.db.cursor.execute(
                    "UPDATE checkouts SET status = 'returned' WHERE user_id = %s AND book_title ILIKE %s AND status = 'active'",
                    (self.current_user_id, f"%{title}%")
                )
                self.db.conn.commit()
                return f"I've processed the return for '{title}'. Thank you!"
            return "Which book would you like to return?"

        elif intent == "borrow_book":
            title = params.get("title", "")
            quantity = params.get("quantity", 1)
            if title and len(title) > 2:
                return self.db.checkout_book(self.current_user_name, self.current_user_id, title, quantity)
            return "Which book would you like to borrow?"

        elif intent == "search_books":
            query = params.get("query", "")
            if query and len(query) > 1:
                return self.db.search_book(query)
            return "What subject or title are you looking for?"

        elif intent == "browse_books":
            self.db.cursor.execute("SELECT title FROM books ORDER BY RANDOM() LIMIT 5")
            books = self.db.cursor.fetchall()
            if books:
                titles = [f"'{b[0]}'" for b in books]
                return "Here are some books: " + ", ".join(titles) + "."
            return "The catalog seems empty right now."

        elif intent == "register":
            name = params.get("name", "")
            if name:
                uid = name.lower().replace(" ", "_")
                self.db.get_or_create_user(uid, name)
                self.current_user_name = name
                self.current_user_id = uid
                return f"Welcome, {name}! You're now registered. How can I help you?"
            return "What's your full name?"
        
        elif intent == "library_stats":
            return self.db.get_library_stats()

        return None  # "chat" intent - use AI fallback

    def get_response(self, user_input):
        print(f"\n📝 User ({self.current_user_name}): {user_input}")

        # Step 1: Let Llama classify the intent
        intent_data = self._classify_intent(user_input)
        print(f"🧠 Intent: {intent_data.get('intent')} | Params: {intent_data.get('params')}")

        
        # Step 2: Try to execute the intent
        
        result = self._execute_intent(intent_data)  # ← USE THIS, not intent_handler
        if result:
            self._save_history(user_input, result)
            print(f"🤖 HOLO: {result}")
            return result

        # Step 3: Fallback to AI chat

        prompt = f"""You are HOLO, a helpful hologram librarian.
Speaking to: {self.current_user_name} (registered member).

For book actions, use tags:
- [SEARCH: keyword] to find books
- [CHECKOUT: title] to borrow a book

Keep responses warm and under 2 sentences.

User: {user_input}
HOLO:"""

        try:
            response = requests.post(
                config.OLLAMA_URL,
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "stop": ["User:", "HOLO:"]}
                },
                timeout=30
            )

            if response.status_code == 200:
                ai_text = response.json().get('response', '').strip()

                # Process any tags the AI might have included
                tag_match = re.search(r'\[(SEARCH|CHECKOUT):\s*(.*?)\]', ai_text)
                if tag_match:
                    action = tag_match.group(1)
                    params = tag_match.group(2).strip()
                    if action == "SEARCH":
                        ai_text = self.db.search_book(params)
                        self.pending_book = params
                    elif action == "CHECKOUT":
                        ai_text = self.db.checkout_book(self.current_user_name, self.current_user_id, params, 1)

                ai_text = ai_text.replace('*', '').strip()
                self._save_history(user_input, ai_text)
                print(f"🤖 HOLO: {ai_text}")
                return ai_text

            return "I am having trouble connecting."
        except Exception as e:
            return f"Error: {e}" 
