from retriever import Retriever

def main():
    r = Retriever()
    while True:
        q = input("Enter query (or 'exit'): ")
        if q.lower() == "exit":
            break
        results = r.query(q)
        print("\n--- RESULTS ---")
        for idx, res in enumerate(results, 1):
            print(f"{idx}. {res[:300]}...\n")

if __name__ == "__main__":
    main()
