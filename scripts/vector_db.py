"""Legacy FAISS entry point kept to prevent accidental index overwrites.

The committed docstore is a Git LFS pointer in this checkout, and the original
index was constructed with `FakeEmbeddings`. Loading it with pickle
deserialization or silently rebuilding it would be unsafe and misleading.
The Gramsaathi One application uses `scripts.retriever.Retriever` instead.
"""


class VectorStores:
    def __init__(self, *args, **kwargs) -> None:
        raise RuntimeError(
            "The legacy FAISS index is not used: its Git LFS docstore is unavailable "
            "and it was built with non-semantic FakeEmbeddings. Use scripts.retriever.Retriever."
        )
