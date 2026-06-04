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
        self.pending_book = None
        self.system_prompt = "You are HOLO, a helpful hologram librarian."
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

    def get_response(self, user_input):
        print(f"\n📝 User ({self.current_user_name}): {user_input}")
        user_lower = user_input.lower()
        
        # 1. Checkouts query
        if any(kw in user_lower for kw in ['my books', 'checked out', 'borrowed', 'what books', 'how many books']):
            self.db.cursor.execute(
                "SELECT book_title, checkout_date, due_date FROM checkouts WHERE user_id = %s AND status = 'active'",
                (self.current_user_id,)
            )
            checkouts = self.db.cursor.fetchall()
            if checkouts:
                books_list = [f"'{t}' (due: {d})" for t, _, d in checkouts]
                result = f"You have {len(checkouts)} book(s): " + "; ".join(books_list) + "."
            else:
                result = "You don't have any books checked out right now."
            self._save_history(user_input, result)
            print(f"🤖 HOLO: {result}")
            return result
        
        # 2. Borrow/checkout
        title_match = re.search(
            r'(?:borrow|check\s*out|checkout|get|grab)\s+(?:a\s+)?(?:book\s+)?(?:called|titled|named\s+)?[\"\']?([^\"\'?!,.]+)',
            user_lower
        )
        if not title_match:
            title_match = re.search(r'[\"\']?([^\"\'?!,]+?)[\"\']?\s+sounds?\s+(?:appealing|good|great|interesting)', user_lower)
        if title_match:
            book_title = title_match.group(1).strip()
            book_title = re.sub(r'\b(?:please|thanks|for me|the book)\b', '', book_title).strip()
            if len(book_title) > 3:
                result = self.db.checkout_book(self.current_user_name, self.current_user_id, book_title)
                self._save_history(user_input, result)
                print(f"🤖 HOLO: {result}")
                return result
        
        # 3. Search
        search_match = re.search(
            r'(?:search|find|look\s*for|do you have|books?\s+(?:about|on|in))\s+[\"\']?([^\"\'?!,.]+)',
            user_lower
        )
        if search_match:
            query = search_match.group(1).strip()
            if len(query) > 2:
                result = self.db.search_book(query)
                self.pending_book = query
                self._save_history(user_input, result)
                print(f"🤖 HOLO: {result}")
                return result
        
        # 4. Confirmation
        if user_lower.strip() in ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'please', 'go ahead', 'proceed']:
            if self.pending_book:
                result = self.db.checkout_book(self.current_user_name, self.current_user_id, self.pending_book)
                self.pending_book = None
                self._save_history(user_input, result)
                print(f"🤖 HOLO: {result}")
                return result
        
        # 5. General conversation
        prompt = f"""You are HOLO, a helpful hologram librarian.

YOU ARE SPEAKING TO: {self.current_user_name}
THEIR ACCOUNT: Active (ID: {self.current_user_id})
YOU KNOW THIS PERSN. They are a registered library member.
When they ask if you know them, say YES and greet them by name: {self.current_user_name}.

For book operations use: [SEARCH: title] or [CHECKOUT: title]
Keep responses under 2 sentences.

User: {user_input}
HOLO:"""
        
        try:
            response = requests.post(
                config.OLLAMA_URL,
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "stop": ["User:", "HOLO:"]}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                ai_text = response.json().get('response', '').strip()
                
                # Process any tags
                tag_match = re.search(r'\[(SEARCH|CHECKOUT):\s*(.*?)\]', ai_text)
                if tag_match:
                    action = tag_match.group(1)
                    params = tag_match.group(2).strip()
                    if action == "SEARCH":
                        ai_text = self.db.search_book(params)
                        self.pending_book = params
                    elif action == "CHECKOUT":
                        ai_text = self.db.checkout_book(self.current_user_name, self.current_user_id, params)
                
                ai_text = ai_text.replace('*', '').strip()
                self._save_history(user_input, ai_text)
                print(f"🤖 HOLO: {ai_text}")
                return ai_text
                
            return "I am having trouble connecting."
        except Exception as e:
            return f"Error: {e}"
