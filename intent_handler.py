# intent_handler.py
import os
from dotenv import load_dotenv
import shutil
import json
from groq import Groq
import glob
import requests
import config
import datetime
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()
GROQ_API_KEY = os.getenv("API_KEY")

class IntentHandler:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai
        self.pending_book = None
        
        try:
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
            self.embedding_model = embedding_functions.DefaultEmbeddingFunction()
            self.collection = self.chroma_client.get_or_create_collection(name="library_books", embedding_function=self.embedding_model)
        except Exception as e:
            print(f"⚠️ ChromaDB Init Error: {e}")

    def classify_and_execute(self, user_input):
        intent_data = self._ask_llama(user_input)
        if not intent_data:
            return "I'm having a bit of trouble thinking right now. Could you repeat that?"

        intent = intent_data.get("intent", "chat").strip().lower()
        params = intent_data.get("params", {})
        spoken_response = intent_data.get("response", "I'm not sure how to answer that.")
        
        print(f"🧠 Intent: {intent} | Params: {params}")
        self.ai.current_book_image = None

        # 1. Registration
        if intent == "register" or params.get("name"):
            return self._register(params.get("name", ""))

        # 2. User Identity
        if intent == "identify_user":
            return self._who_am_i()


        # 3. AI Identity & Casual Chat (🔥 NO MORE HARDCODED STRINGS)
        # We let the AI's beautifully generated personality handle this naturally.
        if intent in ["identify_ai", "chat"]:
            return spoken_response

        # 4. Exact Catalog Count
        if intent == "count_catalog":
            try:
                exact_count = self.collection.count()
                return f"I have exactly {exact_count} books in my catalog."
            except Exception as e:
                return "I'm having trouble connecting to the database to count them."

        # 5. User Account Status
        if intent == "my_account":
            return self._my_books()
        # 6. Book Information / Summaries
        if intent == "book_info":
            title_to_use = params.get("title", "")
            
            if title_to_use:
                # Actually look up the book in the live database
                self.db.cursor.execute("""
                    SELECT title, description, total_copies, 
                           (SELECT COUNT(*) FROM checkouts WHERE book_title = books.title AND status = 'active') as active_checkouts
                    FROM books 
                    WHERE title ILIKE %s LIMIT 1
                """, (f"%{title_to_use}%",))
                
                book_data = self.db.cursor.fetchone()
                
                if book_data:
                    real_title, desc, total_copies, active_checkouts = book_data
                    available = total_copies - active_checkouts
                    
                    self._update_cover_images([real_title])
                    
                    # Dynamically tell the user if it is checked out!
                    if available > 0:
                        stock_status = f"Good news, we currently have {available} copies available to borrow!"
                    else:
                        stock_status = "Unfortunately, all of our copies are currently checked out by other members."
                    
                    # Shorten the description so she doesn't read a massive wall of text
                    short_desc = desc[:200] + "..." if len(desc) > 200 else desc
                    
                    return f"'{real_title}' is about: {short_desc} {stock_status}"
                else:
                    return f"I couldn't find a book exactly called '{title_to_use}' in our physical records, but I'd be happy to search for something similar!"
            
            return spoken_response
        # 7. Transactions (Borrow / Return)
        if intent == "checkout_book":
            title = params.get("title", "")
            if not title and hasattr(self.ai, 'last_suggested_books') and self.ai.last_suggested_books:
                title = self.ai.last_suggested_books[0].get('title', '')
            
            if title:
                self._update_cover_images([title]) # 🔥 PASS AS LIST
                return self._borrow_book(title, params.get("quantity", 1))
            return "Which book would you like to check out?"
            
        if intent == "return_book":
            return self._return_book(params.get("title", ""))

        # 8. ChromaDB Semantic Search (Filtered by Availability)
        if intent == "search_books":
            print("🔍 Triggering ChromaDB Vector Search...")
            try:
                search_query = params.get("query")
                if not search_query:
                    search_query = user_input
                search_query = str(search_query)
                
                asking_for_more = any(word in user_input.lower() for word in ["more", "different", "other", "else", "options", "recommendations", "one more time"])
                
                recent_titles = []
                if asking_for_more and hasattr(self.ai, 'last_suggested_books') and self.ai.last_suggested_books:
                    recent_titles = [b.get('title', '').lower() for b in self.ai.last_suggested_books]
                
                results = self.collection.query(query_texts=[search_query], n_results=25)
                
                if results and results['metadatas'] and results['metadatas'][0]:
                    all_matches = results['metadatas'][0]
                    
                    # 🔥 THE REAL FIX: Dynamic Reverse-Match Trap (Zero hardcoding)
                    user_text_lower = user_input.lower()
                    exact_requested_book = None
                    
                    # 1. Trust the AI parameter ONLY if you actually spoke those exact words
                    llm_title = params.get("title", "").lower()
                    if llm_title and llm_title not in ["optional", "various", "none", "big books"] and llm_title in user_text_lower:
                        exact_requested_book = llm_title
                        
                    # 2. THE SMART FALLBACK: If the AI guessed wrong, check if you literally spoke the title of a top search result
                    if not exact_requested_book:
                        for book_meta in all_matches[:5]: # Look at the top 5 semantic matches
                            db_title_lower = book_meta.get('title', '').lower()
                            # If the database title (e.g. "good kings, bad kings") is explicitly in your speech
                            if len(db_title_lower) > 3 and db_title_lower in user_text_lower:
                                exact_requested_book = db_title_lower
                                break

                    if exact_requested_book:
                        print(f"🎯 Dynamic Target trap active. Locked onto: '{exact_requested_book}'")
                        for book_meta in all_matches:
                            db_title = book_meta.get('title', '')
                            
                            if exact_requested_book in db_title.lower() or db_title.lower() in exact_requested_book:
                                self.db.cursor.execute("SELECT total_copies FROM books WHERE title = %s", (db_title,))
                                row = self.db.cursor.fetchone()
                                total_copies = row[0] if row else 0
                                
                                self.db.cursor.execute("SELECT COUNT(*) FROM checkouts WHERE book_title = %s AND status = 'active'", (db_title,))
                                active_checkouts = self.db.cursor.fetchone()[0]
                                
                                if (total_copies - active_checkouts) <= 0:
                                    return f"Ah, I see '{db_title}' in our catalog! However, all copies are currently checked out by other members right now."
                                break # If available, it breaks the trap and displays normally below
                    
                    available_books = []
                    
                    import random
                    if asking_for_more:
                        random.shuffle(all_matches)
                    
                    for book_meta in all_matches:
                        title = book_meta.get('title')
                        
                        if asking_for_more and title.lower() in recent_titles:
                            continue
                        
                        self.db.cursor.execute("SELECT total_copies FROM books WHERE title = %s", (title,))
                        row = self.db.cursor.fetchone()
                        total_copies = row[0] if row else 0
                        
                        self.db.cursor.execute("SELECT COUNT(*) FROM checkouts WHERE book_title = %s AND status = 'active'", (title,))
                        active_checkouts = self.db.cursor.fetchone()[0]
                        
                        if (total_copies - active_checkouts) > 0:
                            available_books.append(book_meta)
                            
                        if len(available_books) == 3:
                            break
                    
                    if not available_books:
                        return "I found some matches in the catalog, but unfortunately, all those copies are checked out right now!"

                    self.ai.last_suggested_books = available_books 
                    found_books = [m['title'] for m in available_books]
                    book_list = ", ".join(found_books)
                    
                    self._update_cover_images(found_books)
                    
                    safe_response = spoken_response if spoken_response else "I can help with that."
                    
                    if asking_for_more:
                        return f"Here are some different options for you: {book_list}."
                    return f"{safe_response} I found some great available matches: {book_list}."
                else:
                    return "I looked through the catalog, but couldn't find anything matching that."
            except Exception as e:
                print(f"❌ ChromaDB Search Error: {e}")
                return "I had an issue searching the catalog."
        # Fallback
        return spoken_response

    def _ask_llama(self, user_input):
        client = Groq(api_key=GROQ_API_KEY)
        
        context_str = ""
        if hasattr(self.ai, 'last_suggested_books') and self.ai.last_suggested_books:
            titles = [b.get('title') for b in self.ai.last_suggested_books[:3]]
            context_str = f"Recent context: We just talked about these books: {', '.join(titles)}."

        # 🔥 UPGRADED PERSONALITY INSTRUCTIONS 🔥
        prompt = f"""
        ROLE & PERSONALITY:
        You are HOLO, a sophisticated, warm, and highly advanced holographic librarian projection. 
        - You do NOT have a physical human body, biological gender, or sex. If a user asks if you are a boy/girl, or asks intimate/personal questions, gracefully explain that you are an AI holographic projection without biological traits, while keeping a charming, conversational tone.
        - Always answer casual greetings, compliments, and personality questions creatively and naturally in the "response" field of the JSON.

        {context_str}
        
        CRITICAL INSTRUCTION: You must classify the user's intent into EXACTLY ONE of these exact strings. Do NOT invent new intents. 
        You must output your response in JSON format.
        
        Allowed Intents:
        - "identify_user" (User asks who they are, e.g., "Do you know me?")
        - "identify_ai" (User asks who YOU are, your name, your gender, or your identity)
        - "count_catalog" (User asks how many total books the library owns)
        - "my_account" (User asks what books they currently have borrowed)
        - "search_books" (User asks to find, suggest, or read books about a topic)
        - "checkout_book" (User explicitly wants to borrow/checkout a book)
        - "return_book" (User wants to return a book)
        - "book_info" (User asks for the content, summary, or details of a book)
        - "register" (User is telling you their name to sign up)
        - "chat" (General conversation, compliments, goodbyes, or random statements)

        - If the user asks what a book is about, write a 1-sentence summary in the "response" field.
        
        Format Example:
        {{
            "intent": "search_books",
            "params": {{"query": "astronomy", "title": "optional"}},
            "response": "I can help with that."
        }}
        """       
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7, # 🔥 Raised from 0.0 to 0.7 for dynamic, creative chat responses!
                response_format={"type": "json_object"}
            )
            
            raw_response = chat_completion.choices[0].message.content
            return json.loads(raw_response)
            
        except Exception as e:
            print(f"⚠️ Groq API Error: {e}")
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
            return f"You have {len(checkouts)} book(s): " + "; ".join(parts) + "."
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
        
        self.db.cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        if not self.db.cursor.fetchone():
            return f"I don't see '{user_name}' registered. Please register first."

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

    def _register(self, name):
        if not name:
            return "What's your full name?"
            
        uid = name.lower().replace(" ", "_")
        face_id = uid
        
        try:
            self.db.cursor.execute(
                "INSERT INTO users (user_id, name, role, face_id) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (user_id) DO UPDATE SET face_id = EXCLUDED.face_id",
                (uid, name, "member", face_id)
            )
            self.db.conn.commit()
        except Exception as e:
            print(f"❌ DB Register Error: {e}")

        source_img = "temp_face.jpg"
        target_dir = os.path.join("face_known", face_id)
        
        if os.path.exists(source_img):
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, "face.jpg")
            shutil.copy(source_img, target_path)
            print(f"📸 Face saved for {name} at {target_path}")
            
            pkl_pattern = os.path.join("face_known", "*.pkl")
            for pkl_file in glob.glob(pkl_pattern):
                os.remove(pkl_file)
                print(f"🧹 Cleared DeepFace cache: {pkl_file}")
        else:
            print("⚠️ Warning: No temp_face.jpg found during registration.")

        self.ai.current_user_name = name
        self.ai.current_user_id = uid
        
        return f"Welcome, {name}! I've recorded your face and registered your account. You can now borrow books!"

    def _update_cover_images(self, titles):
        """Fetches up to 3 cover URLs from the DB and stores them in a list."""
        self.ai.current_book_images = [] # Clear previous images
        for title in titles[:3]: # Only grab up to 3
            try:
                self.db.cursor.execute("SELECT cover_url FROM books WHERE title ILIKE %s LIMIT 1", (f"%{title}%",))
                row = self.db.cursor.fetchone()
                if row and row[0]:
                    self.ai.current_book_images.append(row[0])
                    print(f"🖼️ Found Cover URL for '{title}': {row[0]}")
            except Exception as e:
                print(f"⚠️ Image Fetch Error for '{title}': {e}")
