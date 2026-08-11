# Aibou (相棒)

A high-performance, local-first AI companion and creative partner built with FastAPI, React, LangChain, ChromaDB, and Ollama.

Aibou is designed to feel like an authentic co-author and intellectual sparring partner: zero corporate bot disclaimers, no sycophantic yes-man behavior, full persistent document memory, real-time voice mode, and an automatic GPU watchdog that frees your VRAM whenever you launch a game.

---

## Key Features

- **Direct Token-by-Token Streaming**: Instant typing responses streamed via WebSockets with zero routing delays.
- **Voice Mode (0 MB VRAM)**: Real-time speech-to-text mic dictation plus natural neural TTS audio streaming with multiple selectable voice personalities.
- **Persistent Document Vector Memory (ChromaDB)**: Attach PDFs, Word docs (`.docx`), text files, or code. Aibou chunks and vectorizes them locally so lore and character facts persist permanently across chats.
- **Automatic GPU Game & VRAM Watchdog**: Automatically detects when heavy 3D games launch (Wuthering Waves, Cyberpunk 2077, Genshin Impact, Elden Ring, Unreal Engine, etc.) and instantly frees 100% of your GPU VRAM.
- **Live Tool Execution**: Real-time web search, math calculations, local project file inspection, and time queries.
- **Preserved Multi-Agent Swarm**: Full LangGraph multi-agent graph (Architect, Coder, Critic, Planner) preserved in the codebase for scaling.

---

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Framer Motion, Lucide Icons, Vanilla CSS
- **Backend**: FastAPI, WebSockets, SQLAlchemy (AsyncPG), LangChain, ChromaDB
- **LLM Runtime**: Ollama (local) or OpenRouter (cloud API)
- **Database**: PostgreSQL (chat history) + ChromaDB (vector embeddings)
- **Voice Engine**: Edge-TTS (streaming neural audio) + Web Speech API (hardware-accelerated STT)

---

## Quickstart & Setup Guide

### Option A: 1-Click Windows Desktop App (Zero Setup)
If you want to use Aibou without touching any code or terminal:
1. Go to the [Releases](https://github.com/may-bach/Aibou/releases) page.
2. Download **`Aibou_1.0.0_x64-setup.exe`**.
3. Run the installer and launch Aibou directly from your desktop.
*(Aibou automatically uses built-in SQLite so no database or Docker installation is needed).*


---

### Option B: Run from Source Code (Developers)

#### 1. Prerequisites
Make sure you have the following installed on your machine:
- **Python 3.10+** (Python 3.11 or 3.12 recommended)
- **Node.js 18+** & npm
- **Ollama** ([ollama.com](https://ollama.com))
- **Docker** (optional: only if using PostgreSQL instead of SQLite)

---

#### 2. Start PostgreSQL (Optional)


Run a local PostgreSQL container in one command:

```bash
docker run --name aibou-postgres -e POSTGRES_USER=aibou -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=aibou_db -p 5432:5432 -d postgres:16-alpine
```

*(If you already have PostgreSQL installed locally, just create a database named `aibou_db` with user `aibou` and password `secret`, or update your `.env` connection string).*

---

### 3. Pull Your Local Models in Ollama

Start the Ollama server and pull the embedding model plus your preferred LLM:

```bash
# Required for vector memory and document search
ollama pull nomic-embed-text

# Recommended local model (fast, fits in 16GB VRAM at 50+ tokens/sec)
ollama pull qwen2.5:14b

# Optional larger models:
# ollama pull mistral-small
# ollama pull gemma2:27b
```

---

### 4. Backend Setup

1. Open your terminal in the project root:
   ```bash
   cd Aibou
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. *(Optional)* Create a `.env` file in the root directory if you want to customize ports or use OpenRouter:
   ```env
   DATABASE_URL=postgresql+asyncpg://aibou:secret@localhost:5432/aibou_db
   USE_LOCAL_LLM=True
   LOCAL_LLM_URL=http://localhost:11434
   LOCAL_LLM_API_KEY=ollama
   ```

5. Start the FastAPI backend server:
   ```bash
   python -m uvicorn main:app --reload
   ```
   *The backend will boot up on `http://localhost:8000` and automatically initialize database tables and the GPU game watchdog.*

---

### 5. Frontend Setup

1. In a new terminal, navigate to the frontend folder:
   ```bash
   cd Aibou/frontend
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open `http://localhost:5173` in your browser.

---

## How It Works

### Voice Mode
- Click the **Mic** button in the chat input to speak directly to Aibou. Speech-to-text runs locally in the browser with 0ms server lag.
- Click the **Listen** button on any assistant message to hear it read aloud using natural neural voices.
- Toggle **Auto Voice** in the top header if you want Aibou to speak every reply automatically.

### Document Attachments & RAG
- Click the **+** button in the chat box to upload `.docx`, `.pdf`, `.txt`, `.md`, or code files.
- Files are parsed, chunked, and saved in your local ChromaDB vector store.
- Aibou seamlessly references your uploaded documents and past lore across different chats.

### Automatic GPU Game Watchdog
- Whenever you launch games like Wuthering Waves, Genshin Impact, Cyberpunk, or 3D rendering engines like Unreal Engine / Blender, Aibou detects the GPU process and evicts itself from VRAM within ~4 seconds.
- You get 100% of your GPU memory for gaming with zero manual effort. When you close the game and chat again, Aibou warms back up.

---

## Cloud Models (Optional)

If you want to run massive 70B+ models or frontier cloud endpoints like DeepSeek V3 or Kimi at 80+ tokens/sec:

1. Add your OpenRouter API key to your `.env` file:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
   USE_LOCAL_LLM=False
   ```
2. Update the model name in `src/core/config.py` (e.g. `deepseek/deepseek-chat` or `qwen/qwen-2.5-72b-instruct`).

---

## Project Structure

```
Aibou/
├── frontend/             # React + Vite + TypeScript frontend
│   ├── src/
│   │   ├── components/   # ChatArea, ChatInput, ChatMessage, Sidebar
│   │   ├── hooks/        # useVoice (STT + TTS management)
│   │   └── index.css     # Dark mode aesthetics & animations
├── src/
│   ├── agents/           # Multi-agent swarm nodes, state, & tools
│   ├── api/routers/      # Chat, Voice, & User endpoints
│   ├── core/             # Configuration & environment settings
│   ├── db/               # PostgreSQL session & database setup
│   ├── models/           # SQLAlchemy user & conversation models
│   ├── prompts/          # Core companion personality & extraction prompts
│   └── services/         # ChromaDB RAG, document parser, & GPU watchdog
├── main.py               # FastAPI entrypoint & lifespan manager
└── requirements.txt      # Python dependencies
```

---

## License

MIT License. Feel free to customize, fork, and build upon Aibou!
