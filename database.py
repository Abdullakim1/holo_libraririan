import psycopg2
import datetime

class LibraryDB:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="holo_library",
            user="postgres",
            password="12345678",
            host="localhost",
            port="5432"
        )
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                total_copies INTEGER NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkouts (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) REFERENCES users(user_id), 
                book_title VARCHAR(255) NOT NULL,
                checkout_date DATE NOT NULL,
                due_date DATE NOT NULL,
                status VARCHAR(20) NOT NULL
            )
        ''')
        self.conn.commit()
        print("✅ PostgreSQL Library Database Ready!")

    def add_user(self, user_id, name, role):
            """Register a new user in the library system"""
            self.cursor.execute('''
                INSERT INTO users (user_id, name, role) 
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            ''', (user_id, name, role))
            self.conn.commit()


    def get_library_stats(self):
        """Returns the actual count of books to stop AI hallucinations."""
        self.cursor.execute("SELECT COUNT(*), SUM(total_copies) FROM books")
        res = self.cursor.fetchone()
        return f"We have {res[0]} unique titles and {res[1] or 0} total physical copies."

    def search_book(self, book_title):
        try:
            self.cursor.execute(
                "SELECT title, total_copies FROM books WHERE LOWER(title) LIKE LOWER(%s) LIMIT 5",
                (f"%{book_title}%",)
            )
            results = self.cursor.fetchall()
            
            if not results:
                return f"I couldn't find any books matching '{book_title}'."
            
            response_parts = []
            for title, total_copies in results:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM checkouts WHERE book_title = %s AND status = 'active'",
                    (title,)
                )
                active_checkouts = self.cursor.fetchone()[0]
                available = total_copies - active_checkouts
                response_parts.append(f"'{title}' ({available}/{total_copies} available)")
            
            return "Results: " + "; ".join(response_parts)
            
        except Exception as e:
            return f"Search error: {str(e)}"

    def checkout_book(self, user_name, user_id, book_title, quantity=1):
        """Checks if user exists and book is available, then processes checkout."""
        
        # STEP 1: Check if user is registered
        self.cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = self.cursor.fetchone()
        
        if not user:
            return f"I don't see '{user_name}' in our library system. Would you like to register?"
        
        # STEP 2: Check if book exists
        self.cursor.execute("SELECT title, total_copies FROM books WHERE LOWER(title) LIKE LOWER(%s)", (f"%{book_title}%",))
        book_results = self.cursor.fetchall()
        
        if not book_results:
            return f"I couldn't find any book matching '{book_title}'."
        
        # Use the first match (or exact match if available)
        real_title = book_results[0][0]
        total_copies = book_results[0][1]
        
        for title, copies in book_results:
            if title.lower() == book_title.lower():
                real_title = title
                total_copies = copies
                break
        
        # STEP 3: Check availability
        self.cursor.execute(
            "SELECT COUNT(*) FROM checkouts WHERE book_title = %s AND status = 'active'", 
            (real_title,)
        )
        active_checkouts = self.cursor.fetchone()[0]
        available_copies = total_copies - active_checkouts
        
        # STEP 4: Check if enough copies available
        if quantity > total_copies:
            return f"We only have {total_copies} copies of '{real_title}' total. I can't check out {quantity}."
        
        if quantity > available_copies:
            return f"Only {available_copies} copy(s) available. Would you like {available_copies} instead of {quantity}?"
        
        # STEP 5: Process checkout
        if available_copies > 0:
            checkout_date = datetime.date.today()
            due_date = checkout_date + datetime.timedelta(days=14)
            
            # Create one checkout record per copy
            for _ in range(quantity):
                self.cursor.execute('''
                    INSERT INTO checkouts (user_id, book_title, checkout_date, due_date, status) 
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, real_title, checkout_date, due_date, 'active'))
            
            self.conn.commit()
            
            remaining = available_copies - quantity
            if quantity == 1:
                return f"You've checked out '{real_title}'. Due: {due_date.strftime('%B %d, %Y')}. ({remaining} copies left)"
            else:
                return f"You've checked out {quantity} copies of '{real_title}'. Due: {due_date.strftime('%B %d, %Y')}. ({remaining} copies left)"
        else:
            return f"Sorry, all {total_copies} copies of '{real_title}' are currently checked out."

    def get_or_create_user(self, user_id, name, role='member'):
        """Get existing user or create new one"""
        self.cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = self.cursor.fetchone()
        
        if user:
            return f"Welcome back, {name}!"
        else:
            self.add_user(user_id, name, role)
            print(f"✅ Registered: {name} (ID: {user_id}, Role: {role})")
            return f"Registration complete! Welcome, {name}."
    def get_user_by_face_id(self, face_id):
        """Look up a user by their face recognition ID"""
        self.cursor.execute(
            "SELECT user_id, name, role FROM users WHERE face_id = %s", 
            (face_id,)
        )
        return self.cursor.fetchone()
    def get_borrowed_books(self, user_id):
        """Fetch all active checkouts for a specific user."""
        try:
            # We only want 'active' checkouts, not history
            query = """
                SELECT book_title, due_date 
                FROM checkouts 
                WHERE user_id = %s AND status = 'active'
            """
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"❌ Database Error in get_borrowed_books: {e}")
            return []
    def return_book(self, user_id, book_title):
        try:
            # 1. Changed "book_id" to "id" for the books table
            # (Note: Using ILIKE since PostgreSQL uses it for case-insensitive searches)
            self.cursor.execute("SELECT id FROM books WHERE title ILIKE %s", (f"%{book_title}%",))
            book = self.cursor.fetchone()
            
            if not book:
                return False, f"I couldn't find '{book_title}' in the library catalog."
            
            # Grab the actual book's ID (the first column returned)
            real_book_id = book[0]

            # 2. Check if the user has this book borrowed
            self.cursor.execute(
                "SELECT * FROM borrowed_books WHERE user_id = %s AND book_id = %s", 
                (user_id, real_book_id)
            )
            if not self.cursor.fetchone():
                return False, f"It doesn't look like you have '{book_title}' checked out."

            # 3. Remove the book from the user's borrowed list
            self.cursor.execute(
                "DELETE FROM borrowed_books WHERE user_id = %s AND book_id = %s", 
                (user_id, real_book_id)
            )
            
            # 4. Increase the available inventory of the book by 1
            # (We use "id" here again for the books table)
            self.cursor.execute(
                "UPDATE books SET available_copies = available_copies + 1 WHERE id = %s", 
                (real_book_id,)
            )
            
            # 5. Fix the connection variable (checking for the most common names)
            if hasattr(self, 'conn'):
                self.conn.commit()
            elif hasattr(self, 'db'):
                self.db.commit()
            else:
                # Fallback to grabbing the connection directly from the cursor
                self.cursor.connection.commit()
                
            return True, f"Successfully returned '{book_title}'. Thank you!"

        except Exception as e:
            print(f"Database error during return: {e}")
            
            # Rollback safely
            if hasattr(self, 'conn'):
                self.conn.rollback()
            elif hasattr(self, 'db'):
                self.db.rollback()
            else:
                self.cursor.connection.rollback()
                
            return False, "There was an error updating the database."
