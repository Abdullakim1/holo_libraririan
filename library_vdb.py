import chromadb
from chromadb.utils import embedding_functions

class LibraryVDB:
    def __init__(self):
        # This saves your data to a folder so it persists
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # Default embedding function (runs locally on your CPU)
        self.model = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="books", 
            embedding_function=self.model
        )

    def add_book(self, book_id, title, description, author):
        # We combine title and description so the AI 'understands' the whole book
        content = f"Title: {title}. Author: {author}. Description: {description}"
        self.collection.add(
            documents=[content],
            metadatas=[{"title": title, "author": author, "id": book_id}],
            ids=[str(book_id)]
        )

    def search_books(self, query_text, n_results=3):
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results['metadatas'][0] # Returns the best matching book info
