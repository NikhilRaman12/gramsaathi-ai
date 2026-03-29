from scripts.vector_db import VectorStores

class Retriever:
    def __init__(self, vector_store=None):
        if vector_store:
            self.vector_store = vector_store
        else:
            self.vector_store = VectorStores().vectorstore

    def get_context(self, question, k=3):
        docs = self.vector_store.similarity_search(question, k=k)
        return "\n".join([doc.page_content for doc in docs])
