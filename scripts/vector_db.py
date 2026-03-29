from langchain_community.vectorstores.faiss import FAISS
from langchain_community.embeddings import FakeEmbeddings
from scripts.chunk_pdfs import chunk_pdfs

INDEX_DIR = "data/faiss_index"

class VectorStores:
    def __init__(self):
        self.embeddings = FakeEmbeddings(size=1536)
        self.vectorstore = self.create_vectorstore()

    def create_vectorstore(self):
        try:
            # Load existing FAISS index safely
            vectorstore = FAISS.load_local(
                INDEX_DIR,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print("Loaded FAISS index from disk.")
        except Exception:
            # Build new index if none exists
            print("Creating new FAISS index...")
            texts = chunk_pdfs()
            vectorstore = FAISS.from_texts(texts, self.embeddings)
            vectorstore.save_local(INDEX_DIR)
            print("Saved FAISS index to disk.")
        return vectorstore
