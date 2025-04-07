import os
from pinecone import Pinecone, ServerlessSpec
from fastapi import HTTPException

# PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENV", "gcp-starter")
TOP_K_DOCUMENTS = 3
INDEX_NAME = "document-indexer1"

# Initialize Pinecone
# pinecone = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
pinecone = Pinecone(api_key='pcsk_neJko_BsRKEKrwsZu1pxagKbrw4jczZVRbyZgu6iQugNparvNiSbQcXPxzuU8Km83VadW')

# Create index if it doesn't exist
if INDEX_NAME not in pinecone.list_indexes().names():
    pinecone.create_index(
        INDEX_NAME,
        dimension=1024,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pinecone.Index(INDEX_NAME)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def add_document_to_db(document_id: str, paragraphs: list[str], embeddings: list[list[float]]):
    try:
        embeddings = [
            (
                f"{document_id}_{i}",  # Vector ID
                embedding,
                {"document_id": document_id, "sentence_id": i, "text": paragraph},
            )
            for i, (paragraph, embedding) in enumerate(zip(paragraphs, embeddings))
        ]
        for embedding_chunk in chunks(embeddings, 100):
            index.upsert(vectors=embedding_chunk)
        return True
    except Exception as e:
        raise HTTPException(404, detail=f"Pinecone indexing fetch fail with error: {e}")


def fetch_top_paragraphs(document_id: str, embedding: list[float]) -> list[str]:
    try:
        query_response = index.query(
            top_k=TOP_K_DOCUMENTS,
            vector=embedding,
            filter={"document_id": {"$eq": document_id}},
            include_metadata=True,
        )
    except Exception as e:
        raise HTTPException(404, detail=f"Pinecone query failed with error: {e}")

    answers = [match["metadata"]["text"] for match in query_response["matches"]]
    return answers
