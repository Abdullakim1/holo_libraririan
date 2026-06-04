# intent_handler.py
import os
import shutil
import glob
import json
import requests
import config
import datetime

class IntentHandler:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai
        self.pending_book = None
    def classify_and_execute(self, user_input):
        """Let Llama classify intent AND generate the chat response in one go"""
        
        intent_data = self._ask_llama(user_input)
        if not intent_data:
            return None

        intent = intent_data.get("intent", "chat")
        params = intent_data.get("params", {})
        
        # 🔥 NEW: Extract the spoken text directly from the JSON!
        spoken_response = intent_data.get("response", "I'm not sure how to answer that.")
        
        print(f"🧠 Intent: {intent} | Params: {params}")

        # Execute based on intent
        if intent == "who_am_i":
            return self._who_am_i()
        elif intent == "my_books":
            return self._my_books()
        elif intent == "return_book":
            return self._return_book(params.get("title", ""))
        elif intent == "borrow_book":
            return self._borrow_book(params.get("title", ""), params.get("quantity", 1))
        elif intent == "search_books":
            return self._search_books(params.get("query", ""))
        elif intent == "browse_books":
            return self._browse_books()
        elif intent == "register":
            return self._register(params.get("name", ""))
        else:
            # 🔥 NEW: If it's just a normal chat, return the generated text immediately!
            return spoken_response 

    def _ask_llama(self, user_input):
        # 🔥 NEW: Tell Llama to include its spoken reply inside the JSON
        prompt = f"""
        You are HOLO, a helpful hologram librarian.
        Analyze the user input and output ONLY valid JSON. 
        You must include a "response" field containing your spoken reply to the user.
        Keep your spoken response friendly but STRICTLY under 15 words.

        Format Example:
        {{
            "intent": "chat",
            "params": {{}},
            "response": "Hello! I am HOLO. How can I help you today?"
        }}

        User: {user_input}
        JSON:"""
        
        try:
            response = requests.post(
                config.OLLAMA_URL,
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0} # Keep it 0.0 so it doesn't hallucinate
                },
                timeout=10
            )
            if response.status_code == 200:
                raw_text = response.json().get('response', '').strip()
                # Find JSON block in the response
                start_idx = raw_text.find('{')
                end_idx = raw_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = raw_text[start_idx:end_idx+1]
                    return json.loads(json_str)
            return None
        except Exception as e:
            print(f"⚠️ Intent Classification Error: {e}")
            return None

    def _who_am_i(self):
        name = self.ai.current_user_name
        if name not in ["Guest", "Unknown"]:
            return f"You're {name}, a registered library member!"
        return "I don't know you yet. Tell me your name to register!"

    def _my_books(self):
        self.db.cursor.execute(
            "SELECT book_title, checkout_date, due_date FROM checkouts WHERE user_id = %s AND status = 'active'",
            (self.ai.current_user_id,)
        )
        checkouts = self.db.cursor.fetchall()
        if checkouts:
            parts = [f"'{t}' (due: {d})" for t, _, d in checkouts]
            return f"You hav {len(checkouts)} book(s): " + "; ".join(parts) + "."
        return "You don't have any books checked out right now."

    def _return_book(self, title):
        if not title:
            return "Which book would you like to return?"
        self.db.cursor.execute(
            "UPDATE checkouts SET status = 'returned' WHERE user_id = %s AND book_title ILIKE %s AND status = 'active'",
            (self.ai.current_user_id, f"%{title}%")
        )
        self.db.conn.commit()
        return f"Return processed for '{title}'. Thank you!"

    def _borrow_book(self, title, quantity=1):
        if not title:
            return "Which book would you like to borrow?"
        
        user_name = self.ai.current_user_name
        user_id = self.ai.current_user_id
        
        # Check user
        self.db.cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        if not self.db.cursor.fetchone():
            return f"I don't see '{user_name}' registered. Please register first."

        # Find book
        self.db.cursor.execute(
            "SELECT title, total_copies FROM books WHERE LOWER(title) LIKE LOWER(%s)",
            (f"%{title}%",)
        )
        results = self.db.cursor.fetchall()
        if not results:
            return f"I couldn't find '{title}' in our library."

        real_title = results[0][0]
        total_copies = results[0][1]
        for t, c in results:
            if t.lower() == title.lower():
                real_title = t
                total_copies = c
                break

        # Check availability
        self.db.cursor.execute(
            "SELECT COUNT(*) FROM checkouts WHERE book_title = %s AND status = 'active'",
            (real_title,)
        )
        active = self.db.cursor.fetchone()[0]
        available = total_copies - active

        if quantity > total_copies:
            return f"We only have {total_copies} copies of '{real_title}' total."
        if quantity > available:
            return f"Only {available} copies available. Want {available} instead?"

        if available > 0:
            checkout_date = datetime.date.today()
            due_date = checkout_date + datetime.timedelta(days=14)
            for _ in range(quantity):
                self.db.cursor.execute(
                    "INSERT INTO checkouts (user_id, book_title, checkout_date, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, real_title, checkout_date, due_date, 'active')
                )
            self.db.conn.commit()
            remaining = available - quantity
            qty = f"{quantity} copies of " if quantity > 1 else ""
            return f"Checked out {qty}'{real_title}'. Due: {due_date.strftime('%B %d, %Y')}. ({remaining} left)"

        return f"Sorry, '{real_title}' is fully checked out."

    def _search_books(self, query):
        if not query:
            return "What are you looking for?"
        return self.db.search_book(query)

    def _browse_books(self):
        self.db.cursor.execute("SELECT title FROM books ORDER BY RANDOM() LIMIT 5")
        books = self.db.cursor.fetchall()
        if books:
            titles = [f"'{b[0]}'" for b in books]
            return "Here are some books: " + ", ".join(titles) + "."
        return "The catalog seems empty."

    def _register(self, name):
            if not name:
                return "What's your full name?"
                
            # 1. Create the unique IDs
            uid = name.lower().replace(" ", "_")
            face_id = uid  # Using the same string for consistency
            
            # 2. Register in the Database
            # Note: We include the face_id column here
            try:
                self.db.cursor.execute(
                    "INSERT INTO users (user_id, name, role, face_id) VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (user_id) DO UPDATE SET face_id = EXCLUDED.face_id",
                    (uid, name, "member", face_id)
                )
                self.db.conn.commit()
            except Exception as e:
                print(f"❌ DB Register Error: {e}")

            # 3. Handle the Physical Face Image
            source_img = "temp_face.jpg"
            target_dir = os.path.join("face_known", face_id)
            
            if os.path.exists(source_img):
                # Create folder: face_known/kim_un/
                os.makedirs(target_dir, exist_ok=True)
                
                # Copy temp_face.jpg -> face_known/kim_un/face.jpg
                target_path = os.path.join(target_dir, "face.jpg")
                shutil.copy(source_img, target_path)
                print(f"📸 Face saved for {name} at {target_path}")
                
                # 🔥 4. CLEAR THE CACHE (Critical for DeepFace)
                # This forces recognize.py to see the new user immediately
                pkl_pattern = os.path.join("face_known", "*.pkl")
                for pkl_file in glob.glob(pkl_pattern):
                    os.remove(pkl_file)
                    print(f"🧹 Cleared DeepFace cache: {pkl_file}")
            else:
                print("⚠️ Warning: No temp_face.jpg found during registration.")

            # 5. Update the AI's current state
            self.ai.current_user_name = name
            self.ai.current_user_id = uid
            
            return f"Welcome, {name}! I've recorded your face and registered your account. You can now borrow books!"
