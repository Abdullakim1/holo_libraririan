import psycopg2
import datetime

class LibraryDB:
    def __init__(self):
        # Update these with your actual PostgreSQL credentials
        self.conn = psycopg2.connect(
            dbname="holo_library",
            user="postgres",       # Default user is usually 'postgres'
            password="12345678",
            host="localhost",
            port="5432"
        )
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Creates the tables if they don't exist yet."""
        
        # 1. Users Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL
            )
        ''')

        # 2. Books Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                total_copies INTEGER NOT NULL
            )
        ''')
        
        # 3. Checkouts Table (Now links to the user_id)
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
        print("✅ PostgreSQL Library Database Ready with Users Table!")

    def add_user(self, user_id, name, role):
        """Register a new user in the library system"""
        # Using ON CONFLICT lets us ignore it if the user already exists
        self.cursor.execute('''
            INSERT INTO users (user_id, name, role) 
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING
        ''', (user_id, name, role))
        self.conn.commit()

    def add_book(self, title, total_copies):
        """Quick helper to add inventory"""
        self.cursor.execute(
            "INSERT INTO books (title, total_copies) VALUES (%s, %s)",
            (title, total_copies)
        )
        self.conn.commit()

    def checkout_book(self, user_name, user_id, book_title):
        """Checks if a book is available and assigns it to the user."""
        
        # 1. Check total copies owned
        self.cursor.execute("SELECT total_copies FROM books WHERE title = %s", (book_title,))
        result = self.cursor.fetchone()
        
        if not result:
            return f"I'm sorry, I don't see '{book_title}' in our library system."
        
        total_copies = result[0]
        
        # 2. Check how many are currently out
        self.cursor.execute(
            "SELECT COUNT(*) FROM checkouts WHERE book_title = %s AND status = 'active'", 
            (book_title,)
        )
        active_checkouts = self.cursor.fetchone()[0]
        
        available_copies = total_copies - active_checkouts
        
        # 3. Process the checkout if available
        if available_copies > 0:
            checkout_date = datetime.date.today()
            due_date = checkout_date + datetime.timedelta(days=14) # 2-week checkout
            
            self.cursor.execute('''
                INSERT INTO checkouts (user_name, user_id, book_title, checkout_date, due_date, status) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_name, user_id, book_title, checkout_date, due_date, 'active'))
            
            self.conn.commit()
            return f"Success! {user_name} has checked out {book_title}. There are {available_copies - 1} copies remaining. It is due on {due_date.strftime('%B %d')}."
            
        else:
            return f"I apologize, but all {total_copies} copies of '{book_title}' are currently checked out by others."
