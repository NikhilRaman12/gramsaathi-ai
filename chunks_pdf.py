# scripts/chunk_pdfs.py
import os

def main():
    data_dir = "data"
    documents = []

    for fname in os.listdir(data_dir):
        if fname.endswith(".pdf"):
            fpath = os.path.join(data_dir, fname)
            try:
                with open(fpath, "rb") as f:
                    content = f.read()
                    if not content.startswith(b"%PDF"):
                        raise ValueError("Invalid PDF header")
                    # Simulate chunks
                    documents.append({"file": fname, "content": content[:100]})
                print(f"Processed: {fpath}")
            except Exception as e:
                print(f"Skipping {fpath} due to error: {e}")

    print(f"Total documents loaded: {len(documents)}")
    return documents

if __name__ == "__main__":
    main()
