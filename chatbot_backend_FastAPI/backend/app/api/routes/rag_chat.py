from fastapi import APIRouter, Form, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from sqlalchemy.orm import Session
from sqlalchemy_utils import Ltree
from app.api.routes.response import get_db, get_current_user
from app.models.chat_message import ChatMessage
from app.models.user import User
from datetime import datetime
import tempfile, os, requests, uuid, re

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

# 🧹 Clean and format LaTeX and markdown for better frontend display
def clean_llm_output(text: str) -> str:
    # First handle the block equations
    text = re.sub(r"\\\[(.*?)\\\]", 
                 lambda match: f"\nEquation:\n{match.group(1)}\n", 
                 text, flags=re.DOTALL)
    
    text = re.sub(r"\$\$(.*?)\$\$", 
                 lambda match: f"\nEquation:\n{match.group(1)}\n", 
                 text, flags=re.DOTALL)
    
    # Then handle inline equations
    text = re.sub(r"\\\((.*?)\\\)", 
                 lambda match: f"({match.group(1)})", 
                 text)
    
    text = re.sub(r"\$(.*?)\$", 
                 lambda match: f"({match.group(1)})", 
                 text)
    
    # Define LaTeX symbol replacements with proper escaping
    latex_symbols = [
        (r"\\times", "×"),
        (r"\\div", "÷"),
        (r"\\pm", "±"),
        (r"\\mp", "∓"),
        (r"\\leq", "≤"),
        (r"\\geq", "≥"),
        (r"\\neq", "≠"),
        (r"\\approx", "≈"),
        (r"\\infty", "∞"),
        (r"\\sum", "Σ"),
        (r"\\prod", "Π"),
        (r"\\int", "∫"),
        (r"\\partial", "∂"),
        (r"\\alpha", "α"),
        (r"\\beta", "β"),
        (r"\\gamma", "γ"),
        (r"\\Delta", "Δ"),
        (r"\\rightarrow", "→"),
        (r"\\leftarrow", "←"),
        (r"\\Rightarrow", "⇒"),
        (r"\\Leftarrow", "⇐"),
        (r"\\leftrightarrow", "↔"),
        (r"\\Leftrightarrow", "⇔"),
        (r"\\forall", "∀"),
        (r"\\exists", "∃"),
        (r"\\in", "∈"),
        (r"\\notin", "∉"),
        (r"\\subset", "⊂"),
        (r"\\subseteq", "⊆"),
        (r"\\cup", "∪"),
        (r"\\cap", "∩"),
        (r"\\emptyset", "∅"),
        (r"\\nabla", "∇"),
        (r"\\cdot", "·"),
        (r"\\sqrt", "√"),
        (r"\\frac{(.*?)}{(.*?)}", r"\1/\2"),  # Handle fractions
        (r"\\vec{(.*?)}", r"vector \1"),
    ]
    
    for pattern, replacement in latex_symbols:
        text = re.sub(pattern, replacement, text)
    
    # Handle text formatting commands
    text = re.sub(r"\\text\{(.*?)\}", r"\1", text)
    text = re.sub(r"\\mathrm\{(.*?)\}", r"\1", text)
    
    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Remove markdown formatting
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    
    # Clean up remaining backslashes
    text = re.sub(r"\\([^a-zA-Z])", r"\1", text)
    
    return text.strip()

# 📥 Upload and vectorize a PDF
@router.post("/rag/upload-doc")
async def upload_doc(file: UploadFile = File(...)):
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        vectorstore = Chroma.from_documents(chunks, embedding=embedding_model)
        doc_id = str(uuid.uuid4())
        save_vectorstore(doc_id, vectorstore)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(tmp_path)

    return JSONResponse(content={"doc_id": doc_id})

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
    parent_id: str = Form(None),
    doc_id: str = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 1. Store user message
    if parent_id:
        parent = db.query(ChatMessage).filter(ChatMessage.id == parent_id, ChatMessage.user_id == user.id).first()
        if not parent:
            return JSONResponse(status_code=404, content={"error": "Parent message not found"})
        ltree_path = f'{parent.ltree_path_str}.{uuid.uuid4().hex[:8]}'
    else:
        ltree_path = uuid.uuid4().hex[:8]
    user_msg = ChatMessage(
        user_id=user.id,
        parent_id=parent_id,
        ltree_path=Ltree(ltree_path),
        content=question,
        is_user=True,
        doc_id=doc_id,
        timestamp=datetime.utcnow(),
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

    # 3. Store AI message as child
    ai_ltree_path = f'{user_msg.ltree_path_str}.{uuid.uuid4().hex[:8]}'
    ai_msg = ChatMessage(
        user_id=user.id,
        parent_id=user_msg.id,
        ltree_path=Ltree(ai_ltree_path),
        content=answer,
        is_user=False,
        doc_id=doc_id,
        timestamp=datetime.utcnow(),
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return JSONResponse(content={
        "user_message": {
            "id": str(user_msg.id),
            "content": user_msg.content,
            "parent_id": str(user_msg.parent_id) if user_msg.parent_id else None,
            "ltree_path": user_msg.ltree_path_str,
            "is_user": True,
            "timestamp": user_msg.timestamp.isoformat(),
            "doc_id": user_msg.doc_id,
        },
        "ai_message": {
            "id": str(ai_msg.id),
            "content": ai_msg.content,
            "parent_id": str(ai_msg.parent_id),
            "ltree_path": ai_msg.ltree_path_str,
            "is_user": False,
            "timestamp": ai_msg.timestamp.isoformat(),
            "doc_id": ai_msg.doc_id,
        }
    })

@router.get("/chat/tree")
def get_chat_tree(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    
    print("this api hitted")
    """
    Returns all chat messages for the current user, with ltree_path as a string.
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
            "parent_id": str(msg.parent_id) if msg.parent_id else None,
            "ltree_path": str(msg.ltree_path),
            "content": msg.content,
            "is_user": msg.is_user,
            "timestamp": msg.timestamp.isoformat(),
            "doc_id": msg.doc_id,
        }
        for msg in messages
    ]
