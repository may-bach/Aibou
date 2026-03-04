import re
from pathlib import Path
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.agents.state import AibouState
from src.core.config import settings


coder_llm = ChatOpenAI(
    model=settings.MODEL_CODING,
    base_url=f"{settings.LOCAL_LLM_URL}/v1",
    api_key="ollama",
    temperature=0.2
)

CODER_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "node_prompts" / "coder.md"
with open(CODER_PROMPT_PATH, "r", encoding="utf-8") as file:
    CODER_PROMPT = file.read()

async def coder_node(state: AibouState) -> dict:
    print("[NODE] Coder is writing...")
    
    messages = state.get("messages", [])
    prompt_sequence = [SystemMessage(content=CODER_PROMPT)] + list(messages)
    
    response = await coder_llm.ainvoke(prompt_sequence)
    response_text = response.content
    
    code_blocks = re.findall(r"```[\w]*\n(.*?)```", response_text, re.DOTALL)
    new_artifacts = {}
    current_workspace_code = ""
    
    if code_blocks:
        current_workspace_code = code_blocks[0].strip()
        first_line = current_workspace_code.split('\n')[0]
        
        if "filename:" in first_line.lower():
            raw_filename = first_line.split(":")[-1].strip()
            filename = re.sub(r'[^a-zA-Z0-9_.-]', '', raw_filename)
            new_artifacts[filename] = current_workspace_code

    return {
        "messages": [AIMessage(content=response_text)], 
        "current_agent": "Coder",                       
        "current_code": current_workspace_code,         
        "artifacts": new_artifacts,                     
        "retry_count": state.get("retry_count", 0) + 1  
    }