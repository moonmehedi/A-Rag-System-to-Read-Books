# 🤖 A-RAG-System-to-Read-Books

A sophisticated **Retrieval-Augmented Generation (RAG)** chatbot system with nested conversation threading for enhanced context awareness and topic management. This project combines modern AI/ML technologies with an intuitive user interface to create an intelligent document Q&A system.

## 🎯 **What It Does**

This system enables users to:

- **📚 Upload PDF Documents**: Upload and process PDF files for AI-powered Q&A 
- **💬 Interactive Chat**: Ask questions about uploaded documents with context-aware responses
- **🌳 Nested Conversations**: Create branching conversations from selected text snippets for deeper topic exploration
- **🔍 Smart Context Retrieval**: Automatically finds relevant document sections to answer questions
- **⚡ Real-time Streaming**: Get AI responses in real-time with streaming technology
- **👥 User Management**: Secure authentication and personalized chat history 
- **📱 Responsive UI**: Modern, mobile-friendly interface with shadcn/ui components

## 🛠️ **Technology Stack**

### **Backend (FastAPI + Python)**
| Technology | Purpose | Version |
|------------|---------|---------|
| **FastAPI** | Web framework | Latest |
| **PostgreSQL** | Database | 16 |
| **SQLAlchemy** | ORM | 2.0+ |
| **Alembic** | Database migrations | Latest |
| **LangChain** | RAG framework | 0.3+ |
| **ChromaDB** | Vector database | 1.0+ |
| **HuggingFace** | Embeddings & LLM | Latest |
| **Sentence Transformers** | Text embeddings | 5.0+ |
| **PyPDF** | PDF processing | Latest |
| **Passlib + BCrypt** | Authentication | Latest |
| **PyJWT** | JWT tokens | Latest |
| **Docker** | Containerization | Latest |

### **Frontend (Next.js + TypeScript)**
| Technology | Purpose | Version |
|------------|---------|---------|
| **Next.js** | React framework | 15.2+ |
| **TypeScript** | Type safety | Latest |
| **TailwindCSS** | Styling | Latest |
| **shadcn/ui** | UI components | Latest |
| **Radix UI** | Primitive components | Latest |
| **Lucide React** | Icons | Latest |
| **class-variance-authority** | Component variants | Latest |

### **AI/ML Components**
| Component | Technology | Model/Service |
|-----------|------------|---------------|
| **Embeddings** | HuggingFace | `sentence-transformers/all-MiniLM-L6-v2` |
| **LLM** | HuggingFace API | `deepseek/deepseek-v3-0324` |
| **Vector Store** | ChromaDB | In-memory + persistent |
| **Text Splitting** | LangChain | `RecursiveCharacterTextSplitter` |
| **PDF Processing** | PyPDF | Document loading |

## 🧠 **Prompt Engineering Applied**

### **1. RAG System Prompt**
```python
prompt = f"""You are a helpful assistant. Use the following context to answer the question:

{context}

Question: {question}"""
```

**Engineering Features:**
- **Context Injection**: Relevant document chunks are dynamically inserted
- **Clear Role Definition**: Assistant role with specific instruction to use provided context
- **Structured Format**: Clean separation between context and question

### **2. Context-Aware Responses**
- **Document-Specific Answers**: Responses are grounded in uploaded document content
- **Relevance Filtering**: Only retrieves most relevant document sections
- **Chunk Optimization**: Uses 1000 character chunks with 100 character overlap for optimal context

### **3. Conversation Memory**
- **Chat History Integration**: Maintains conversation context across multiple turns
- **Nested Context Handling**: Preserves context when creating sub-conversations from selected text

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   AI Services   │
│   (Next.js)     │────│   (FastAPI)      │────│  (HuggingFace)  │
│                 │    │                  │    │                 │
│ • Chat UI       │    │ • RAG API        │    │ • Embeddings    │
│ • PDF Upload    │    │ • Auth System    │    │ • LLM API       │
│ • Nested Chats  │    │ • Vector Store   │    │ • Text Models   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         └──────────────│   PostgreSQL     │─────────────┘
                        │   Database       │
                        │                  │
                        │ • Users          │
                        │ • Chat Messages  │
                        │ • Sessions       │
                        └──────────────────┘
```

## 🚀 **Key Features**

### **📄 Document Processing Pipeline**
1. **PDF Upload** → **Text Extraction** → **Chunking** → **Embedding** → **Vector Storage**
2. **Smart Chunking**: Optimized chunk sizes for better context retrieval
3. **Semantic Search**: Vector similarity search for relevant document sections

### **💬 Advanced Chat System**
- **Nested Conversations**: Create sub-chats from selected text snippets
- **Context Preservation**: Maintains conversation history and document context
- **Real-time Streaming**: Token-by-token response streaming
- **LaTeX Support**: Preserves mathematical expressions in responses

### **🔐 Security & Authentication**
- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: BCrypt encryption
- **User Sessions**: Persistent login state
- **API Protection**: All endpoints secured with auth middleware

### **🎨 Modern UI/UX**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Mode**: Theme support with next-themes
- **Smooth Animations**: Framer Motion-powered transitions
- **Accessibility**: ARIA-compliant components

## 📁 **Project Structure**

```
A-Rag-System-to-Read-Books/
├── 📂 chatbot_backend_FastAPI/
│   └── 📂 backend/
│       ├── 📂 app/
│       │   ├── 📂 api/routes/    # API endpoints
│       │   ├── 📂 core/          # Configuration
│       │   ├── 📂 db/            # Database setup
│       │   ├── 📂 models/        # SQLAlchemy models
│       │   └── 📂 schemas/       # Pydantic schemas
│       ├── 📂 alembic/           # Database migrations
│       ├── 🐳 docker-compose.yml # PostgreSQL container
│       └── 📋 requirements.txt   # Python dependencies
├── 📂 frontend-nested-chat-interface/
│   ├── 📂 app/                   # Next.js app router
│   ├── 📂 components/            # React components
│   ├── 📂 hooks/                 # Custom React hooks
│   ├── 📂 lib/                   # Utility functions
│   └── 📋 package.json           # Node.js dependencies
├── 🔐 .env                       # Environment variables
├── 📝 .env.example               # Environment template
├── 📚 ENVIRONMENT_SETUP.md       # Setup guide
└── 📖 README.md                  # This file
```

## ⚙️ **Installation & Setup**

### **Prerequisites**
- 🐍 Python 3.11+
- 🟢 Node.js 18+
- 🐳 Docker & Docker Compose
- 🔑 HuggingFace API Key
- 🔗 LangChain API Key

### **1. Environment Setup**
```bash
# Clone the repository
git clone https://github.com/moonmehedi/A-Rag-System-to-Read-Books.git
cd A-Rag-System-to-Read-Books

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### **2. Backend Setup**
```bash
cd chatbot_backend_FastAPI/backend

# Start PostgreSQL database
docker-compose up -d

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload
```

### **3. Frontend Setup**
```bash
cd frontend-nested-chat-interface

# Install dependencies
npm install

# Start development server
npm run dev
```

### **4. Access the Application**
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📊 **API Docs**: http://localhost:8000/docs

## 🔧 **Environment Variables**

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `HUGGINGFACE_TOKEN` | HuggingFace API token | ✅ |
| `LANGCHAIN_API_KEY` | LangChain API key | ✅ |
| `JWT_SECRET_KEY` | JWT signing secret | ✅ |
| `GITHUB_TOKEN` | GitHub API token (optional) | ❌ |

## 📈 **Usage**

1. **🔐 Register/Login**: Create an account or sign in
2. **📄 Upload Document**: Upload a PDF file for processing
3. **💬 Start Chatting**: Ask questions about your document
4. **🌳 Create Sub-chats**: Select text to create focused conversations
5. **📚 Explore Context**: Navigate through nested conversation threads

## 🧪 **Advanced Features**

### **Nested Conversation Threading**
- **Text Selection**: Highlight any text in responses to create sub-conversations
- **Context Inheritance**: Sub-chats maintain parent conversation context
- **Visual Navigation**: Tree-like interface for exploring conversation branches

### **RAG Enhancement**
- **Semantic Chunking**: Intelligent document splitting for optimal retrieval
- **Multi-document Support**: Handle multiple PDFs simultaneously
- **Context Ranking**: Advanced relevance scoring for document chunks

### **Real-time Features**
- **Streaming Responses**: See AI responses as they're generated
- **Live Document Processing**: Real-time PDF upload and indexing
- **Dynamic Context Updates**: Context awareness updates in real-time

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **LangChain**: For the powerful RAG framework
- **HuggingFace**: For state-of-the-art AI models
- **shadcn/ui**: For beautiful, accessible UI components
- **FastAPI**: For the lightning-fast backend framework
- **Next.js**: For the modern React framework

## 🔗 **Links**

- **🏠 Homepage**: [GitHub Repository](https://github.com/moonmehedi/A-Rag-System-to-Read-Books)
- **📚 Documentation**: [Setup Guide](ENVIRONMENT_SETUP.md)
- **🐛 Issues**: [Report Bugs](https://github.com/moonmehedi/A-Rag-System-to-Read-Books/issues)
- **💡 Features**: [Request Features](https://github.com/moonmehedi/A-Rag-System-to-Read-Books/issues)

---

**Made with ❤️ by [moonmehedi](https://github.com/moonmehedi)**

*A research project for improving chatbot context awareness and topic management through nested conversation threading.*
