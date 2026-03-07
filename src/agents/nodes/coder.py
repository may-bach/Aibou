import re
from pathlib import Path
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.agents.state import AibouState
from src.core.config import settings


coder_llm = ChatOpenAI(
    model=settings.MODEL_CODING,
    base_url=f"{settings.LOCAL_LLM_URL}/v1",
    api_key=settings.LOCAL_LLM_API_KEY,
    temperature=0.2,
    timeout=120,
    max_tokens=4096
)

CODER_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "node_prompts" / "coder.md"
with open(CODER_PROMPT_PATH, "r", encoding="utf-8") as file:
    CODER_PROMPT = file.read()

async def coder_node(state: AibouState) -> dict:
    print("[NODE] Coder is writing...")
    
    messages = state.get("messages", [])
    retry_count = state.get("retry_count", 0)
    if retry_count > 0 and len(messages) > 3:
        trimmed_messages = [messages[0]] + list(messages[-2:])
    else:
        trimmed_messages = list(messages)
    
    prompt_sequence = [SystemMessage(content=CODER_PROMPT)] + trimmed_messages
    
    response = await coder_llm.ainvoke(prompt_sequence)
    response_text = response.content
    
    code_blocks = re.findall(r"```[\w]*\n(.*?)```", response_text, re.DOTALL)
    new_artifacts = {}
    current_workspace_code = ""
    
    if code_blocks:
        raw_code = code_blocks[0].strip()
        lines = raw_code.split('\n')
        
        # LLMs occasionally wrap the filename inside the code block with markdown backticks
        first_line_clean = lines[0].strip(" `\r\t")
        
        if "filename:" in first_line_clean.lower():
            raw_filename = first_line_clean.split(":")[-1].strip()
            filename = re.sub(r'[^a-zA-Z0-9_.-]', '', raw_filename)
            
            # Exclude the "filename:" line from the actual python script that gets executed!
            current_workspace_code = "\n".join(lines[1:]).strip()
            
            new_artifacts[filename] = current_workspace_code
        else:
            current_workspace_code = raw_code

    return {
        "messages": [AIMessage(content=response_text)], 
        "current_agent": "Coder",                       
        "current_code": current_workspace_code,         
        "artifacts": new_artifacts,                     
        "retry_count": state.get("retry_count", 0) + 1  
    }