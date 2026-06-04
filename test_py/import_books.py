# import_books.py
import csv
import psycopg2
import sys

def import_goodbooks_csv(csv_file, db_config):
    """
    Import books from goodbooks-10k CSV.
    Expected columns: title, authors, average_rating, isbn, isbn13, etc.
    """
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    count = 0
    errors = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Map CSV columns 
                title = row.get('title', 'Unknown Title')
                author = row.get('authors', 'Unknown Author')
                isbn = row.get('isbn') or row.get('isbn13', '')
                
                # Skip rows with no usable data
                if not title or title == 'Unknown Title':
                    errors += 1
                    continue
                
                # Use ON CONFLICT to avoid duplicates and add copies
                cursor.execute('''
                    INSERT INTO books (title, author, total_copies, isbn)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (title) DO UPDATE 
                    SET total_copies = books.total_copies + 1
                ''', (title, author, 3, isbn)) # Starts each book with 3 copies
                
                count += 1
                if count % 100 == 0:
                    conn.commit()
                    print(f"✅ Processed {count} books...")
                    
            except Exception as e:
                errors += 1
                if errors < 5: # Only print first few errors
                    print(f"Error on row: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"\n🎉 Import complete! Added {count} books. ({errors} errors)")

if __name__ == "__main__":
    db_config = {
        "dbname": "holo_library",
        "user": "postgres",
        "password": "12345678",
        "host": "localhost",
        "port": "5432"
    }
    
    if len(sys.argv) > 1:
        import_goodbooks_csv(sys.argv[1], db_config)
    else:
        print("Usage: python import_books.py books.csv")
