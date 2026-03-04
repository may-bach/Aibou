import asyncio
import tempfile
from src.agents.state import AibouState

async def execution_node(state: AibouState) -> dict:
    print("[NODE] Execution (Sandbox) is running...")
    
    current_code = state.get("current_code", "")
    if not current_code:
        return {"execution_output": "Error: No code provided to execute.", "current_agent": "Executor"}
        
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(current_code)
        temp_filepath = temp_file.name
        
    try:
        process = await asyncio.create_subprocess_exec(
            'python', temp_filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        output = stdout.decode() if stdout else ""
        error = stderr.decode() if stderr else ""
        
        execution_output = output if not error else f"TRACEBACK ERROR:\n{error}"
        
    except Exception as e:
        execution_output = f"Execution failed: {str(e)}"
        
    return {
        "execution_output": execution_output,
        "current_agent": "Executor",
        "requires_human_approval": False 
    }