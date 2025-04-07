from fastapi import FastAPI, UploadFile, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from rag.query_engine import add_document, get_answer
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import nltk
from dotenv import load_dotenv
import os
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.inmemory import InMemoryBackend
from typing import List, Optional

load_dotenv()  # take environment variables from .env.
FastAPICache.init(backend=InMemoryBackend())

nltk.download('punkt')

app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")

templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preload documents into the vector database
PRELOADED_DOCUMENTS = {
    "doc1": "/Users/saian/Panaroma/Insruction Manuals/IM_AH_HH_English_2011.pdf",
    "doc2": "/Users/saian/Panaroma/Insruction Manuals/IM_HL_English_2011.pdf",
    "doc3": "/Users/saian/Panaroma/Insruction Manuals/IM_NPR_English.pdf",
}

DOCUMENT_IDS = {}

@app.on_event("startup")
def preload_documents():
    global DOCUMENT_IDS
    for doc_name, doc_path in PRELOADED_DOCUMENTS.items():
        try:
            document_id = add_document(doc_path)
            DOCUMENT_IDS[doc_name] = document_id
            print(f"Preloaded {doc_name} with ID: {document_id}")
        except Exception as e:
            print(f"Failed to preload {doc_name}: {e}")


class QuestionModel(BaseModel):
    document_id: str
    question: str
    chat_history: Optional[List[dict]] = None  # Add chat history as an optional field


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_document(request: Request, file: UploadFile):
    with tempfile.NamedTemporaryFile(suffix=file.filename) as tmp:
        tmp.write(file.file.read())
        document_id = add_document(tmp.name)
    return {"message": "Document uploaded successfully!", "document_id": document_id}


@app.post("/ask", response_class=HTMLResponse)
async def ask_question(request: Request, document_id: str = Form(...), question: str = Form(...)):
    answer = get_answer(question, document_id)
    return {"document_id": document_id, "question": question, "answer": answer}


@app.post('/api/answer_question')
async def answer_question(req: QuestionModel):
    try:
        # Pass the chat history to the get_answer function
        combined_context = []
        for document_id in DOCUMENT_IDS.values():
            combined_context.append(get_answer(req.question, document_id, req.chat_history))
        
        # Combine all answers into a single string
        final_answer = " ".join(combined_context)
        return {'answer': final_answer}
    except HTTPException as e:
        return {'error': e.detail}  # Return error details as JSON
    except Exception as e:
        return {'error': str(e)}  # Catch unexpected errors and return as JSON


@app.post('/api/upload_document')
async def upload_document(file: UploadFile):
    with tempfile.NamedTemporaryFile(suffix=file.filename) as tmp:
        tmp.write(file.file.read())
        return {'document_id': add_document(tmp.name)}


@app.get('/api/test')
async def test():
    return {'Ping': 'Pong'}
