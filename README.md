# Aibou (相棒)

**A Personal AI Life Companion & Assisstant.**

---

## 1. Project Overview
Aibou is a sophisticated AI agent designed to act as a proactive life companion. Unlike standard chatbots that react to single prompts, Aibou operates as a **persistent cognitive system**; that is, it retains context, plans ahead, and initiates actions based on user goals.

The core philosophy is **Stateful Intelligence**. Most AI tools have amnesia; Aibou is built with a permanent memory layer (SQL + Vector) that allows it to learn from the user's past to inform future assistance.

## 2. Core Capabilities
Aibou is designed to handle the complexity of daily life through specialized modules:

* **Active Planning:** Breaks down vague user goals (e.g., "Prepare for my interview") into concrete, scheduled tasks.
* **Deep Contextual Memory:** Recalls not just facts, but user preferences, past decisions, and emotional context.
* **Reflective Companionship:** Provides feedback and emotional support, distinguishing it from purely transactional to do apps.
* **Systemic Analysis:** Analyzes patterns in user data like finances or habits to offer proactive insights.

## 3. Architecture (The "Brain")
Aibou implements a **Multi Agent System** using **LangGraph**. Instead of a single LLM trying to do everything, specialized agents collaborate:

* **The Orchestrator:** Routes incoming requests to the correct specialist.
* **The Planner:** Decomposes complex tasks.
* **The Critic:** Reviews plans for feasibility and hallucinations.
* **The Memory Manager:** Decides what information is worth storing long-term.

## 4. Technical Stack
* **Orchestration:** LangGraph (Stateful Multi Agent Workflows)
* **Backend:** FastAPI (High performance Async API)
* **Database:** MySQL (Async SQLAlchemy) + Alembic
* **Infrastructure:** Docker & Docker Compose (Planned)
