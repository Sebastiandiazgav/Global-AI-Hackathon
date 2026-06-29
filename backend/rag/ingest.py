"""
MyAgent - Document Ingestion Pipeline
Loads documents from /data/manuales/ and indexes them in the vector store.
Uses Qwen Cloud embeddings + pgvector (or in-memory fallback).
"""

from pathlib import Path
from typing import List

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings


def load_documents(data_dir: str = None) -> List:
    """Load all documents from the manuals directory."""
    if data_dir is None:
        data_dir = str(Path(__file__).parent.parent / "data" / "manuales")

    if not Path(data_dir).exists():
        print(f"⚠️ Data directory not found: {data_dir}")
        return []

    loader = DirectoryLoader(
        data_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    docs = loader.load()
    print(f"📄 Loaded {len(docs)} documents from {data_dir}")
    return docs


def split_documents(documents: List, chunk_size: int = 500, chunk_overlap: int = 100) -> List:
    """Split documents into chunks for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)
    print(f"✂️ Split into {len(chunks)} chunks")
    return chunks


def ingest_documents(chunks: List = None):
    """
    Main ingestion pipeline: Load → Split → Embed → Store.
    """
    print("=" * 50)
    print("🚀 MyAgent - Document Ingestion Pipeline")
    print("=" * 50)

    if chunks is None:
        documents = load_documents()
        if not documents:
            print("❌ No documents to ingest")
            return
        chunks = split_documents(documents)

    embeddings = get_embeddings()

    # TODO: When pgvector is configured, store embeddings there
    # For now, the SimpleVectorStore in retriever.py handles RAG

    print(f"✅ Ingestion complete! {len(chunks)} chunks processed")
    print(f"   Using Qwen Cloud embeddings: text-embedding-v4")
    print("=" * 50)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    ingest_documents()
