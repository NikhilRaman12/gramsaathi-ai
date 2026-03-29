from PyPDF2 import PdfReader
import os

DATA_DIR = "data"

def chunk_pdfs():
    all_chunks = []
    for file in os.listdir(DATA_DIR):
        if file.endswith(".pdf"):
            try:
                reader = PdfReader(os.path.join(DATA_DIR, file))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        all_chunks.append(text.strip())
            except Exception as e:
                print(f"Skipping {file} due to error: {e}")
    return all_chunks
