from nltk.tokenize import sent_tokenize
from rag.file_helper import read_document_from_file
import uuid
from rag.llm_helper import fetch_embeddings, synthesize_answer
from rag.vectordb import add_document_to_db, fetch_top_paragraphs
from fastapi import HTTPException


def split_document_to_paragraphs(document: str, paragraph_len: int = 1000) -> list[str]:
    sentences = sent_tokenize(document)  # Split the paragraph by sentences

    paragraphs = []
    paragraph = ''
    for sentence in sentences:
        paragraph += ' ' + sentence
        if len(paragraph) >= paragraph_len:
            paragraphs.append(paragraph)
            paragraph = ''

    if len(paragraph) > 0:
        paragraphs.append(paragraph)

    return paragraphs


def add_document(filepath: str) -> str:
    document_text = read_document_from_file(filepath)
    paragraphs = split_document_to_paragraphs(document_text)
    if len(paragraphs) == 0:
        raise HTTPException(
            '404', detail='No text was extracted from the document')
    print(len(paragraphs))
    embeddings = fetch_embeddings(paragraphs, embedding_type='search_document')
    document_id = str(uuid.uuid4())
    add_document_to_db(document_id, paragraphs, embeddings)
    return document_id


def get_answer(question: str, document_id: str, chat_history: list[dict] = None):
    # Fetch the embedding for the question
    embedding = fetch_embeddings([question], embedding_type='search_query')[0]
    
    # Fetch relevant paragraphs from the document
    relevant_paragraphs = fetch_top_paragraphs(document_id, embedding)
    if len(relevant_paragraphs) == 0:
        raise HTTPException(
            404, detail=f"No relevant paragraphs found for document ID: {document_id}"
        )
    
    # Prepare the context by combining chat history and relevant paragraphs
    context = []
    if chat_history:
        # Format chat history as a continuous conversation
        for chat in chat_history:
            context.append(f"Q: {chat['question']}\nA: {chat['answer']}")
    
    # Add the current question to the context
    context.append(f"Q: {question}")
    
    # Add a separator and relevant paragraphs from the document
    context.append("Relevant information from the document:")
    context.extend(relevant_paragraphs)
    
    # Synthesize the answer using the combined context
    return synthesize_answer(question, context)
