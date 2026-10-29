# 🤖 Multimodal AI Personal Assistant (MVP)

A full-stack, beginner-friendly **Multimodal AI Personal Assistant** with conversational memory, image understanding, speech-to-text, neural text-to-speech, live cited web search, Retrieval-Augmented Generation (RAG) with PostgreSQL & pgvector, an interactive document workspace with versioning, and emotional assistance with crisis safeguards (including India's 112 emergency hotline).

---

## 🌟 Key Features

1. **Multimodal Interactions**:
   - **Text**: Persistent conversation history with memory.
   - **Vision**: Upload images (`.png`, `.jpg`, `.webp`) and ask visual questions.
   - **Voice Input (STT)**: Browser microphone recording or audio file upload (`.wav`, `.mp3`) with transcription.
   - **Voice Output (TTS)**: Realistic neural audio playback via `edge-tts` (100% free, no API key needed).
2. **Retrieval-Augmented Generation (RAG)**:
   - Ingests `.pdf`, `.txt`, and `.docx` files.
   - Chunks text and generates vector embeddings.
   - High-speed cosine similarity search powered by **PostgreSQL + pgvector** (with automatic zero-setup SQLite fallback).
   - Grounded responses with document name, page, and chunk citations.
3. **Dedicated Web Search**:
   - Live information retrieval using **DuckDuckGo Search** (free, no API key needed) or Tavily.
   - Clickable markdown citations `[Source Title](URL)` with transparent source attribution.
4. **Interactive Document Workspace**:
   - Create new documents from scratch or prompts.
   - AI-assisted refinement: **Summarize**, **Fix Grammar & Tone**, **Expand**, and **Custom Rewrites**.
   - Side-by-side proposed changes preview before applying.
   - Version history tracking with non-destructive saves (never overwrites original files).
   - Automatic RAG re-indexing when updated documents are saved.
   - Download documents as `.txt`.
5. **Personal Emotional Assistance & Safety**:
   - Empathetic, supportive, non-judgmental conversational mode.
   - Clear non-clinical boundaries (disclaims medical diagnosis).
   - Rule-based safety interceptor for self-harm / crisis detection: immediately surfaces **112 (India National Emergency)**, KIRAN, Vandrevala Foundation, and Tele-MANAS helplines.
   - Privacy guard: sensitive emotional dialogues are strictly blocked from external web search APIs.
6. **Application Security**:
   - Environment variable isolation (`.env` in `.gitignore`, `.env.example` provided).
   - Safe server-side UUID filenames preventing directory traversal.
   - Whitelisted MIME types and file extensions (< 15MB).
   - Endpoint rate limiting using `slowapi`.

---

## 🏗️ Architecture & Data Flow

```text
               +-------------------------------------------------+
               |         React + Vite Frontend (Port 5173)       |
               |   [Chat UI | Voice Mic | Vision | Doc Workspace] |
               +-----------------------+-------------------------+
                                       | HTTP / Fetch API
                                       v
               +-------------------------------------------------+
               |           FastAPI Backend (Port 8000)           |
               |  [/chat, /chat/voice, /chat/image, /documents]  |
               +-----------------------+-------------------------+
                                       |
        +------------------------------+-------------------------------+
        |                              |                               |
        v                              v                               v
+------------------+         +-------------------+           +-------------------+
|   AI Services    |         | PostgreSQL +      |           | External Tools    |
| - Gemini / OpenAI|         | pgvector Database |           | - DuckDuckGo /    |
| - Edge-TTS (Free)|         | - conversations   |           |   Tavily Search   |
| - Embeddings     |         | - messages        |           +-------------------+
+------------------+         | - documents       |
                             | - document_chunks |
                             +-------------------+
```

---

## 🧰 Technology Stack

- **Frontend**: React 18, Vite, Vanilla CSS, Native Fetch API, MediaRecorder API
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy, Uvicorn, SlowAPI
- **Database**: PostgreSQL 15+ with `pgvector` extension (with auto-fallback to SQLite for test environments)
- **AI Models**: Google Gemini (`gemini-1.5-flash`), OpenAI (`gpt-4o-mini`)
- **Speech**: `edge-tts` (TTS), Gemini Multimodal Audio / OpenAI Whisper (STT)
- **Web Search**: `duckduckgo-search` (free, no API key required)
- **Document Parsers**: `pypdf`, `python-docx`
- **Testing UI**: Streamlit (`streamlit_app/app.py`)

---

## 📁 Project Structure

```text
mm-chatbot/
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git exclusions
├── docker-compose.yml            # 1-click PostgreSQL with pgvector container
├── README.md                     # This documentation
│
├── database/
│   └── schema.sql                # PostgreSQL + pgvector schema definition
│
├── backend/
│   ├── requirements.txt          # Python packages
│   ├── .env.example              # Backend environment template
│   ├── uploads/                  # Safe storage directory for uploaded files
│   └── app/
│       ├── main.py               # FastAPI entrypoint, middleware, CORS
│       ├── config.py             # App configuration via Pydantic Settings
│       ├── db/
│       │   ├── session.py        # Async SQLAlchemy engine & session factory
│       │   └── init_db.py        # Table and pgvector initialization
│       ├── models/               # SQLAlchemy ORM models
│       │   ├── conversation.py   # Conversation & Message models
│       │   ├── document.py       # Document & DocumentVersion models
│       │   └── chunk.py          # DocumentChunk with Vector embedding
│       ├── schemas/              # Pydantic schemas (Chat, Document, Health)
│       ├── api/                  # API routers
│       │   ├── health.py         # GET /health
│       │   ├── chat.py           # POST /chat, /chat/voice, /chat/image
│       │   ├── documents.py      # CRUD, upload, AI edit, versioning
│       │   └── search.py         # POST /search
│       └── services/             # Core business logic
│           ├── llm_service.py    # LLM integration (Gemini / OpenAI)
│           ├── vision_service.py # Image validation & analysis
│           ├── speech_service.py # STT (Whisper/Gemini) & TTS (Edge-TTS)
│           ├── rag_service.py    # Chunking, vector indexing & search
│           ├── search_service.py # DuckDuckGo web search
│           ├── document_service.py # TXT, PDF, DOCX parsers
│           └── emotional_support_service.py # Empathetic persona & 112 crisis guard
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx               # Main React container with split workspace
│       ├── main.jsx              # React DOM entrypoint
│       ├── index.css             # Responsive styling & crisis alerts
│       ├── services/
│       │   └── api.js            # Fetch API client
│       └── components/
│           ├── ChatArea.jsx      # Message feed & auto-scroll
│           ├── MessageInput.jsx  # Text input, camera upload, mic recorder
│           ├── AudioPlayer.jsx   # TTS voice player
│           ├── SourcesView.jsx   # Citations & source badges
│           ├── CrisisAlert.jsx   # Emergency support alert
│           └── DocumentWorkspace.jsx # Document editor, AI rewrite, versions
│
└── streamlit_app/
    └── app.py                    # Optional developer playground for testing
```

---

## 🚀 Getting Started (Windows PowerShell Setup)

Follow these step-by-step instructions to get the application running on your local machine.

### Prerequisites
- **Python 3.10+** (verify with `python --version`)
- **Node.js 18+ & npm** (verify with `node -v` and `npm -v`)
- Optional: **Docker Desktop** (if you want local PostgreSQL with pgvector)

---

### Step 1: Database Setup

You have three easy options for PostgreSQL with pgvector:

#### Option A: Docker (Recommended for local dev)
In a PowerShell terminal run:
```powershell
docker compose up -d
```
This spins up PostgreSQL 16 with pgvector on port `5432` with username `postgres` and password `password`.

#### Option B: Cloud PostgreSQL (Free & Instant)
Create a free account on [Neon.tech](https://neon.tech) or [Supabase.com](https://supabase.com). Copy your connection string (with pgvector enabled).

#### Option C: Zero-Config Fallback
If you don't have PostgreSQL installed, the backend will automatically initialize a local SQLite database for development, allowing you to test all features immediately.

---

### Step 2: Configure Environment Variables

1. Copy `.env.example` to `backend/.env`:
   ```powershell
   Copy-Item .env.example backend/.env
   ```
2. Open `backend/.env` and configure your API keys:
   ```env
   # Database URL
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mm_assistant

   # Gemini API Key (Get free key from https://aistudio.google.com/)
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=AIzaSy...
   LLM_MODEL=gemini-1.5-flash

   # Text-to-Speech (Free, no API key needed!)
   TTS_PROVIDER=edge-tts
   TTS_VOICE=en-US-JennyNeural

   # Web Search (Free, no API key needed!)
   SEARCH_PROVIDER=duckduckgo
   ```

---

### Step 3: Start the Backend (Terminal 1)

Open a PowerShell terminal in the project directory:

```powershell
# Navigate to backend directory
cd "d:\C Desktop\Ai training\mm-chatbot\backend"

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Start FastAPI with Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 4: Start the Frontend (Terminal 2)

Open a **second** PowerShell terminal:

```powershell
# Navigate to frontend directory
cd "d:\C Desktop\Ai training\mm-chatbot\frontend"

# Start the Vite development server
npm run dev
```

Open your browser at **[http://localhost:5173](http://localhost:5173)** to use the assistant!

---

### Step 5: (Optional) Run the Streamlit Playground (Terminal 3)

If you wish to test individual backend endpoints in isolation:

```powershell
cd "d:\C Desktop\Ai training\mm-chatbot"
.\backend\venv\Scripts\Activate.ps1
streamlit run streamlit_app/app.py
```

---

## 📖 How to Use the Application

### 1. Text Conversations
Type any question in the input bar and press **Enter** or click **➤**. The assistant remembers your conversation history.

### 2. Vision (Image Questions)
Click the **📷** icon, pick an image (`.jpg`, `.png`, `.webp`), type your question (e.g., *"What is written on this invoice?"* or *"Describe this diagram"*), and click send.

### 3. Voice Recording & Playback
- Click the **🎙️** icon to start recording from your microphone. Click it again to stop and send.
- Click the **🔊** icon in the input box to enable audio responses. Assistant messages will include a **▶ Listen** button to play neural audio.

### 4. Grounded Document RAG
1. Click **📄 Workspace Open** in the top header.
2. Click **+ Upload** and select a `.pdf`, `.txt`, or `.docx` file.
3. The file will be extracted, chunked, and embedded into pgvector.
4. In the chat, ask any question about the document (e.g. *"Summarize section 3 of the uploaded document"*). The assistant will cite the document name and chunk references.

### 5. Live Web Search
Click the **🌐 Web Search OFF** button to toggle it to **ON**. Ask questions about current events or live information (e.g. *"Who won the latest Premier League match?"*). The assistant will fetch web results and cite clickable source URLs.

### 6. Document Workspace & Versioning
- Select a document from the workspace dropdown.
- Click **✨ Summarize**, **📝 Fix Grammar**, or **🔍 Expand** to generate AI improvements.
- Review the proposed preview and click **Accept & Replace**.
- Click **✓ Save New Version** to save changes as a new version.
- The document's RAG index is automatically synchronized with the new version!
- Click **💾 Download .TXT** to export your document.

### 7. Emotional Care Mode & Crisis Safeguards
- Click **💖 Emotional Care OFF** to toggle it to **ON**.
- The assistant adopts a compassionate, supportive tone focused on active listening and gentle coping exercises.
- **Safety**: If the user inputs messages indicating crisis or self-harm, a deterministic safety shield displays crisis helplines, including **112 (National Emergency in India)**, and urges connecting with emergency professionals immediately. Private emotional messages are never sent to web search.

---

## 🔒 Security & Best Practices

- **Zero Hardcoded Secrets**: All keys reside in `.env` (which is excluded from Git via `.gitignore`).
- **Path Traversal Defense**: Uploaded files receive safe UUID filenames stored in `backend/uploads/`.
- **RAG Prompt Injection Mitigation**: Retrieved document chunks are wrapped in `<retrieved_documents_context>` XML tags and treated strictly as untrusted reference material.
- **Rate Limiting**: Built-in slowapi rate limiter prevents abuse of expensive endpoints.
- **Single-User Prototype Notice**: This MVP is designed for local single-user prototyping and does not implement multi-tenant auth or isolation.

---

## 🛠️ Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **"FastAPI Connecting / Degraded"** | Backend is not running on port 8000 | Run `uvicorn app.main:app --reload` in `backend/` |
| **"⚠️ Gemini API Key Required"** | Missing API key in `backend/.env` | Add `GEMINI_API_KEY=AIzaSy...` in `backend/.env` and restart |
| **"Microphone access error"** | Browser mic permission denied | Allow microphone permissions in browser URL bar settings |
| **"Database connection error"** | PostgreSQL container is offline | Run `docker compose up -d` or use the automatic SQLite fallback |
| **"CORS error in browser console"** | Origin mismatch | Ensure frontend is running on `http://localhost:5173` |

---

## 📄 License
MIT License. Built for educational and personal assistant prototyping.
