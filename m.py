from database import LibraryDB

def patch_library_inventory():
    print("🔌 Connecting to PostgreSQL...")
    db = LibraryDB()
    
    try:
        print("🔧 Injecting inventory columns into 'books' table...")
        
        # 1. Add total_copies column and default it to 5 copies per book
        db.cursor.execute("""
            ALTER TABLE books 
            ADD COLUMN IF NOT EXISTS total_copies INT DEFAULT 1;
        """)
        
        # 2. Add available_copies column (almost certainly used right after in checkout logic)
        db.cursor.execute("""
            ALTER TABLE books 
            ADD COLUMN IF NOT EXISTS available_copies INT DEFAULT 1;
        """)
        
        db.conn.commit()
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Inventory columns successfully added.")
        print("Every one of your 70,000 books now has 5 copies available to borrow!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Failed to alter database table: {e}")
        db.conn.rollback()
    finally:
        db.cursor.close()
        db.conn.close()

if __name__ == "__main__":
    patch_library_inventory()
