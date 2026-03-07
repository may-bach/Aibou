import asyncio
import os
import tempfile
import shutil
import ast
import sys
from src.agents.state import AibouState

def extract_dependencies(code: str) -> list[str]:
    """Parse the AST to determine external imports that need pip installing."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    deps = set()
    # sys.stdlib_module_names is available in Python 3.10+
    builtins = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_module = alias.name.split('.')[0]
                if base_module not in builtins and not base_module.startswith('_'):
                    deps.add(base_module)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_module = node.module.split('.')[0]
                if base_module not in builtins and not base_module.startswith('_'):
                    deps.add(base_module)
                    
    return list(deps)

async def execution_node(state: AibouState) -> dict:
    print("\n[NODE: EXECUTOR] Setting up ephemeral sandbox...")
    
    current_code = state.get("current_code", "")
    if not current_code:
        return {"execution_output": "Error: No code provided to execute.", "current_agent": "Executor", "requires_human_approval": False}
        
    deps = extract_dependencies(current_code)
    execution_output = ""
    
    # Use mkdtemp so we can ensure totally async cleanup
    temp_dir = tempfile.mkdtemp(prefix="aibou_sandbox_")
    try:
        # 1. Create venv
        print(f"[EXECUTOR] Bootstrapping virtual environment...")
        venv_proc = await asyncio.create_subprocess_exec(
            'python', '-m', 'venv', 'venv',
            cwd=temp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await venv_proc.communicate()
        
        # 2. Resolve paths
        if os.name == 'nt':
            pip_path = os.path.join(temp_dir, 'venv', 'Scripts', 'pip.exe')
            python_path = os.path.join(temp_dir, 'venv', 'Scripts', 'python.exe')
        else:
            pip_path = os.path.join(temp_dir, 'venv', 'bin', 'pip')
            python_path = os.path.join(temp_dir, 'venv', 'bin', 'python')
            
        # 3. Dynamic Dependency Installation
        if deps:
            print(f"[EXECUTOR] Installing dependencies: {', '.join(deps)}")
            pip_proc = await asyncio.create_subprocess_exec(
                pip_path, 'install', *deps,
                cwd=temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            pip_stdout, pip_stderr = await pip_proc.communicate()
            
            if pip_proc.returncode != 0:
                error_msg = pip_stderr.decode() if pip_stderr else "Unknown pip error during install"
                execution_output = f"TRACEBACK ERROR:\nFailed to provision dependencies ({', '.join(deps)}):\n{error_msg}"
                return {
                    "execution_output": execution_output,
                    "current_agent": "Executor",
                    "requires_human_approval": False
                }
                
        # 4. Save and Execute Script
        script_path = os.path.join(temp_dir, 'script.py')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(current_code)
            
        print(f"[EXECUTOR] Executing code (30s timeout restriction)...")
        exec_proc = await asyncio.create_subprocess_exec(
            python_path, 'script.py',
            cwd=temp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # 5. Strict Wait
            stdout, stderr = await asyncio.wait_for(exec_proc.communicate(), timeout=30.0)
            output = stdout.decode('utf-8', errors='replace') if stdout else ""
            error = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            execution_output = output if not error else f"TRACEBACK ERROR:\n{error}"
        except asyncio.TimeoutError:
            try:
                exec_proc.kill()
            except OSError:
                pass
            execution_output = "TRACEBACK ERROR:\nExecution timed out after 30 seconds. Infinite loop or long-running process aborted."
            
    except Exception as e:
        execution_output = f"Sandbox framework failed: {str(e)}"
    finally:
        # 6. Aggressive Cleanup
        print(f"[EXECUTOR] Tearing down ephemeral sandbox...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    return {
        "execution_output": execution_output,
        "current_agent": "Executor",
        "requires_human_approval": False 
    }