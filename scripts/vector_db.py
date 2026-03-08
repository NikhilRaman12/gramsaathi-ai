import os
from pypdf import PdfReader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings

DATA_DIR = "data"


def load_texts():
    texts = []

    for file in os.listdir(DATA_DIR):
        if file.endswith(".pdf"):
            path = os.path.join(DATA_DIR, file)
            print(f"Reading {file}")

            reader = PdfReader(path)

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    texts.append(text)

    print(f"Loaded {len(texts)} text chunks")
    return texts


class VectorStores:

    def __init__(self):
        self.embeddings = FakeEmbeddings(size=1536)
        self.vectorstore = self.create_vectorstore()

    def create_vectorstore(self):

        print("Creating FAISS vector store (memory only)...")

        texts = load_texts()

        vectorstore = FAISS.from_texts(texts, self.embeddings)

        print("Vector store ready.")

        return vectorstore


if __name__ == "__main__":
    VectorStores()
