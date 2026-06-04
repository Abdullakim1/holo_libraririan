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
        self.pending_registration = None
        self.pending_book = None
        self.user_favorites = [] # 🔥 NEW: Store what this user likes
        self.last_suggested_books = []  # 🔥 Remember what we suggested
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

        history = self.db.get_borrowed_books(self.current_user_id)
        if history:
            self.user_favorites = [b[0] for b in history]
        else:
            self.user_favorites = []

    def generate_face_recognition_greeting(self, name):
            """Triggered immediately when a face is recognized to generate a personalized greeting."""
            # 1. Log the user in and load their history/favorites
            self.identify_user(name)
            
            # 2. Build a specialized prompt for a proactive greeting
            history_context = ""
            if self.user_favorites:
                history_context = f"The user has previously read: {', '.join(self.user_favorites)}."
            else:
                history_context = "The user has no reading history yet; they might be new or haven't checked anything out."

            prompt = f"""You are HOLO, a helpful hologram librarian.
    You just scanned the face of: {self.current_user_name}.
    {history_context}

    CRITICAL INSTRUCTION:
    Greet them warmly by name. Proactively mention their past reading tastes or ask if they are back for more books in those specific genres (e.g., sci-fi, horror, history, biology, chemistry) based on what they've read. If they have no history, ask what genres they like.

    Keep the response warm, enthusiastic, and under 3 sentences.

    HOLO:"""

            try:
                response = requests.post(
                    config.OLLAMA_URL,
                    json={
                        "model": config.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7, "stop": ["User:", "HOLO:"]}
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    ai_text = response.json().get('response', '').strip()
                    # Save it to history so HOLO remembers she just said hi
                    self._save_history("System: Face Detected", ai_text)
                    return ai_text
            except Exception as e:
                print(f"❌ Greeting generation error: {e}")
            
            # Fallback if Ollama is lagging
            return f"Hello {name}! Welcome back to the library. What are we looking for today?"

    def _save_history(self, user_input, response):
        self.conversation_history.append({"role": "User", "content": user_input})
        self.conversation_history.append({"role": "HOLO", "content": response})
        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


'''    def _execute_intent(self, intent_data):
        """Execute the database action based on intent"""
        intent = intent_data.get("intent", "chat")
        params = intent_data.get("params", {})
        user_input = self.conversation_history[-1]['content'] if self.conversation_history else ""

        if intent == "library_stats":
            return self.db.get_library_stats()

        elif intent == "who_am_i":
            if self.current_user_name not in ["Guest", "Unknown"]:
                return f"You're {self.current_user_name}, a registered library member!"
            return "I don't know you yet. Tell me your name to register!"

        elif intent == "my_books":
            borrowed_books = self.db.get_borrowed_books(self.current_user_id)
            if not borrowed_books:
                return "You don't have any books checked out right now."
            
            response = "You currently have these books:\n"
            for row in borrowed_books:
                title, due_date = row[0], row[1]
                response += f"• {title} (Due: {due_date})\n"
            return response

        elif intent == "return_book":
            title = params.get("title", "").lower()
            
            # Logic check: Did the user ask a question instead of naming a book?
            invalid_titles = ["what", "how many", "everything", "all", "unknown"]
            is_question = any(word in title for word in invalid_titles) or len(title) < 3

            if is_question:
                books = self.db.get_borrowed_books(self.current_user_id)
                if not books: return "You don't have any books to return!"
                list_str = ", ".join([b[0] for b in books])
                return f"You currently have: {list_str}. Which one would you like to return?"

            success = self.db.return_book(self.current_user_id, title)
            if success:
                return f"Return processed for '{title.title()}'. Thank you!"
            return f"I couldn't find '{title}' in your borrowed list."
        elif intent == "borrow_book":
            title = params.get("title", "")
            quantity = params.get("quantity", 1)
            if title and len(title) > 2:
                return self.db.checkout_book(self.current_user_name, self.current_user_id, title, quantity)
            return "Which book would you like to borrow?"

        elif intent == "search_books":
            query = params.get("query", "")
            if query and len(query) > 0:
                result = self.db.search_book(query)
                # 🔥 Remember what we found
                if "Results:" in result:
                    self.last_suggested_books = [result]
                return result
            return "What subject or title are you looking for?"

        elif intent == "browse_books":
            self.db.cursor.execute("SELECT title FROM books ORDER BY RANDOM() LIMIT 5")
            books = self.db.cursor.fetchall()
            if books:
                titles = [f"'{b[0]}'" for b in books]
                self.last_suggested_books = [b[0] for b in books]  # 🔥 Remember
                return "Here are some books: " + ", ".join(titles) + "."
            return "The catalog seems empty."

        elif intent == "register":
                    name = params.get("name", "")
                    user_id_input = params.get("user_id", "") # Llama needs to extract this
                    role_input = params.get("role", "")       # Llama needs to extract this

                    # Step 1: Start registration / Get Name
                    if not self.pending_registration and name:
                        self.pending_registration = {"name": name, "user_id": None, "role": None}
                        return f"Nice to meet you, {name}! To complete your library card, what is your Student or Faculty ID number?"

                    # Step 2: Get ID
                    if self.pending_registration and not self.pending_registration["user_id"]:
                        # If Llama didn't catch the ID in params, try to find a number in user_input
                        raw_id = "".join(filter(str.isalnum, user_input)) if not user_id_input else user_id_input
                        self.pending_registration["user_id"] = raw_id
                        return "Got it. And are you a Student, Faculty, or a regular Member?"

                    # Step 3: Get Role & Finalize
                    if self.pending_registration and self.pending_registration["user_id"]:
                        role = role_input if role_input else user_input.strip().lower()
                        name = self.pending_registration["name"]
                        uid = self.pending_registration["user_id"]
                        
                        # --- START DATABASE & IMAGE SAVE ---
                        import os, shutil, glob
                        face_id = name.lower().replace(" ", "_")
                        
                        try:
                            self.db.cursor.execute(
                                "INSERT INTO users (user_id, name, role, face_id) VALUES (%s, %s, %s, %s)",
                                (uid, name, role, face_id)
                            )
                            self.db.conn.commit()
                        except Exception as e:
                            print(f"❌ DB Error: {e}")

                        # Save the face image (the code we wrote before)
                        source_img = "temp_face.jpg"
                        target_dir = os.path.join("face_known", face_id)
                        if os.path.exists(source_img):
                            os.makedirs(target_dir, exist_ok=True)
                            shutil.copy(source_img, os.path.join(target_dir, "face.jpg"))
                            for pkl in glob.glob(os.path.join("face_known", "*.pkl")): os.remove(pkl)
                        
                        # Reset state
                        self.pending_registration = None
                        self.current_user_name = name
                        self.current_user_id = uid
                        
                        return f"Registration complete! Welcome to the library, {name}. Your ID {uid} is now linked to your face."

                    return "What is your full name for the registration?" '''
                
