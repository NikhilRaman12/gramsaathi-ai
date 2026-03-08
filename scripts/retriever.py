from vector_db import VectorStores

class Retriever:
    def __init__(self):
        self.vectorstore = VectorStores().vectorstore

    def query(self, q, top_k=2):
        results = self.vectorstore.similarity_search(q, k=top_k)
        return [r.page_content for r in results]
