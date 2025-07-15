from fastapi import APIRouter, Form, UploadFile, File, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy.orm import Session
from app.api.routes.response import get_db, get_current_user
from app.models.chat_message import ChatMessage
from app.models.user import User
from datetime import datetime
import tempfile, os, requests, uuid, re, json, asyncio

router = APIRouter()
load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
API_URL = "https://router.huggingface.co/novita/v3/openai/chat/completions"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# 🧠 HuggingFace Embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 📦 In-memory store (for demo purposes)
doc_vectorstores = {}

def save_vectorstore(doc_id, vectorstore):
    doc_vectorstores[doc_id] = vectorstore

def get_vectorstore(doc_id):
    return doc_vectorstores.get(doc_id)

#  Call Hugging Face-hosted LLM with prompt
def call_hf_llm(context: str, question: str):
    prompt = f"""You are a helpful assistant. Use the following context to answer the question:\n\n{context}\n\nQuestion: {question}"""
    
    payload = {
        "model": "deepseek/deepseek-v3-0324",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        try:
            print(response.json()["choices"][0]["message"]["content"])
            return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return f"Unexpected response format: {response.json()}"
    else:
        return f"Error: {response.status_code} - {response.text}"

# 🌊 Stream LLM response token by token
def stream_hf_llm(context: str, question: str):
    prompt = f"""You are a helpful assistant. Use the following context to answer the question:\n\n{context}\n\nQuestion: {question}"""
    
    payload = {
        "model": "deepseek/deepseek-v3-0324",
        "messages": [{"role": "user", "content": prompt}],
        "stream": True
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, stream=True)
        if response.status_code == 200:
            buffer = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        if data == '[DONE]':
                            break
                        try:
                            json_data = json.loads(data)
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                delta = json_data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    token = delta['content']
                                    buffer += token
                                    
                                    # Check if buffer contains complete words
                                    if ' ' in buffer or '\n' in buffer or len(buffer) > 20:
                                        yield buffer
                                        buffer = ""
                                    elif buffer.endswith(('.', '!', '?', ':', ';', ',', ')', '}', ']', '"', "'")):
                                        yield buffer
                                        buffer = ""
                        except json.JSONDecodeError:
                            continue
            
            # Yield any remaining content in buffer
            if buffer:
                yield buffer
        else:
            yield f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        yield f"Error: {str(e)}"

# 🧹 Clean and format LaTeX and markdown for better frontend display
def clean_llm_output(text: str) -> str:
    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Remove most markdown formatting but keep important ones
    text = re.sub(r"\*\*([^*]+)\*\*", r"**\1**", text)  # Keep bold
    text = re.sub(r"\*([^*]+)\*", r"*\1*", text)  # Keep italic
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)  # Remove headers
    
    # Keep LaTeX expressions as they are - don't clean them
    # Frontend will handle LaTeX rendering
    
    return text.strip()

# 📥 Upload and vectorize a PDF
@router.post("/rag/upload-doc")
async def upload_doc(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are supported"})
    
    # Save file temporarily
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Load and process PDF
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        
        if not documents:
            return JSONResponse(status_code=400, content={"error": "No content found in PDF"})
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        
        if not chunks:
            return JSONResponse(status_code=400, content={"error": "Failed to process PDF content"})
        
        vectorstore = Chroma.from_documents(chunks, embedding=embedding_model)
        doc_id = str(uuid.uuid4())
        save_vectorstore(doc_id, vectorstore)
        
        return JSONResponse(content={"doc_id": doc_id, "message": "PDF uploaded and processed successfully"})
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"Error processing PDF: {str(e)}"})
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

#  Ask a question over a previously uploaded doc
@router.post("/rag/ask-doc")
async def rag_ask_doc(question: str = Form(...), doc_id: str = Form(...)):
    vectorstore = get_vectorstore(doc_id)
    if not vectorstore:
        return JSONResponse(status_code=404, content={"error": "Document not found. Please upload and chunk the PDF first."})

    retriever = vectorstore.as_retriever()
    docs = retriever.invoke(question)
    context = "\n\n".join([doc.page_content for doc in docs])

    # LLM call
    answer = call_hf_llm(context, question)
    answer = clean_llm_output(answer)

    return JSONResponse(content={"answer": answer})

@router.post("/rag/chat")
async def rag_chat(
    question: str = Form(...),
    doc_id: str = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 1. Store user message
    user_msg = ChatMessage(
        user_id=user.id,
        content=question,
        is_user=True,
        doc_id=doc_id,
        timestamp=datetime.now(),
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. Generate AI response
    if doc_id:
        vectorstore = get_vectorstore(doc_id)
        if not vectorstore:
            return JSONResponse(status_code=404, content={"error": "Document not found"})
        retriever = vectorstore.as_retriever()
        docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])
        answer = call_hf_llm(context, question)
    else:
        answer = call_hf_llm("", question)
    answer = clean_llm_output(answer)

    # 3. Store AI message
    ai_msg = ChatMessage(
        user_id=user.id,
        content=answer,
        is_user=False,
        doc_id=doc_id,
        timestamp=datetime.now(),
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return JSONResponse(content={
        "user_message": {
            "id": str(user_msg.id),
            "content": user_msg.content,
            "is_user": True,
            "timestamp": user_msg.timestamp.isoformat(),
            "doc_id": user_msg.doc_id,
        },
        "ai_message": {
            "id": str(ai_msg.id),
            "content": ai_msg.content,
            "is_user": False,
            "timestamp": ai_msg.timestamp.isoformat(),
            "doc_id": ai_msg.doc_id,
        }
    })

@router.post("/rag/chat/stream")
async def rag_chat_stream(
    question: str = Form(...),
    doc_id: str = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 1. Store user message
    user_msg = ChatMessage(
        user_id=user.id,
        content=question,
        is_user=True,
        doc_id=doc_id,
        timestamp=datetime.now(),
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. Prepare context if doc_id provided
    context = ""
    if doc_id:
        vectorstore = get_vectorstore(doc_id)
        if not vectorstore:
            return JSONResponse(status_code=404, content={"error": "Document not found"})
        retriever = vectorstore.as_retriever()
        docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])

    # 3. Create streaming response
    async def generate_stream():
        # First, send user message
        yield f"data: {json.dumps({'type': 'user_message', 'data': {'id': str(user_msg.id), 'content': user_msg.content, 'is_user': True, 'timestamp': user_msg.timestamp.isoformat(), 'doc_id': user_msg.doc_id}})}\n\n"
        
        # Then stream AI response
        full_response = ""
        ai_msg_id = str(uuid.uuid4())
        
        # Send AI message start
        yield f"data: {json.dumps({'type': 'ai_message_start', 'data': {'id': ai_msg_id, 'timestamp': datetime.now().isoformat()}})}\n\n"
        
        # Stream tokens with better spacing
        for token_chunk in stream_hf_llm(context, question):
            # Don't clean individual tokens, just append them
            full_response += token_chunk
            yield f"data: {json.dumps({'type': 'token', 'data': {'content': token_chunk}})}\n\n"
            await asyncio.sleep(0.05)  # Slightly longer delay for better readability
        
        # Only clean the full response at the end (but preserve LaTeX)
        # full_response = clean_llm_output(full_response)
        
        # Store AI message in database
        ai_msg = ChatMessage(
            user_id=user.id,
            content=full_response,
            is_user=False,
            doc_id=doc_id,
            timestamp=datetime.now(),
        )
        db.add(ai_msg)
        db.commit()
        db.refresh(ai_msg)
        
        # Send completion signal with full response (not cleaned to preserve LaTeX)
        yield f"data: {json.dumps({'type': 'ai_message_complete', 'data': {'id': str(ai_msg.id), 'content': full_response, 'timestamp': ai_msg.timestamp.isoformat()}})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@router.get("/chat/messages")
def get_chat_messages(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Returns all chat messages for the current user.
    """
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.timestamp)
        .all()
    )
    return [
        {
            "id": str(msg.id),
            "content": msg.content,
            "is_user": msg.is_user,
            "timestamp": msg.timestamp.isoformat(),
            "doc_id": msg.doc_id,
        }
        for msg in messages
    ]
